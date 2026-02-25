<?php
defined( 'ABSPATH' ) || exit;

/**
 * Minimal pure-PHP PDF text extractor.
 *
 * Supports text-based PDFs (not scanned images).
 * Extracts text from content streams by decoding BT...ET blocks.
 * Each PDF page becomes one slide.
 */
class Pitchdeck_PDF_Parser {

    /**
     * Parse a .pdf file and return an array of slide data structs.
     *
     * @param string $file_path Absolute path to the .pdf file.
     * @return array
     * @throws RuntimeException If the file cannot be read or has no extractable text.
     */
    public static function parse( string $file_path ): array {
        $raw = file_get_contents( $file_path );
        if ( false === $raw ) {
            throw new RuntimeException( "Cannot read PDF file: {$file_path}" );
        }

        if ( substr( $raw, 0, 4 ) !== '%PDF' ) {
            throw new RuntimeException( 'File does not appear to be a valid PDF.' );
        }

        $pages = self::extract_pages( $raw );

        if ( empty( $pages ) ) {
            throw new RuntimeException( 'No text content found in the PDF. The file may contain only images.' );
        }

        $slides = [];
        foreach ( $pages as $index => $text ) {
            $slides[] = [
                'slide_number' => $index + 1,
                'slide_text'   => $text,
                'extra_info'   => '',
            ];
        }

        return $slides;
    }

    /**
     * Extract text grouped by page from the raw PDF binary.
     *
     * Strategy:
     * 1. Find all content stream objects (between "stream" and "endstream").
     * 2. Decode FlateDecode compressed streams if zlib is available.
     * 3. Extract text from BT...ET blocks inside each stream.
     * 4. Associate streams with pages via the PDF object/page tree.
     *
     * Because building a full PDF object tree is complex, we use a simpler
     * heuristic: collect all streams in document order and split them across
     * pages by counting /Page dictionary entries.
     *
     * @param string $raw Full PDF binary content.
     * @return string[]   Array of page text strings.
     */
    private static function extract_pages( string $raw ): array {
        // Count pages declared in the PDF.
        $page_count = self::count_pages( $raw );

        // Extract all content streams in document order.
        $streams = self::extract_streams( $raw );

        if ( empty( $streams ) ) {
            return [];
        }

        // Pull text from each stream.
        $stream_texts = [];
        foreach ( $streams as $stream ) {
            $text = self::text_from_stream( $stream );
            if ( '' !== $text ) {
                $stream_texts[] = $text;
            }
        }

        if ( empty( $stream_texts ) ) {
            return [];
        }

        // Distribute streams evenly across pages.
        if ( $page_count <= 1 || count( $stream_texts ) <= $page_count ) {
            // One stream per page (or fewer streams than pages).
            return $stream_texts;
        }

        // Multiple streams per page — chunk them.
        $chunks     = array_chunk( $stream_texts, (int) ceil( count( $stream_texts ) / $page_count ) );
        $pages      = [];
        foreach ( $chunks as $chunk ) {
            $pages[] = implode( "\n", $chunk );
        }

        return $pages;
    }

    /**
     * Count the number of pages in the PDF via /Count entry in the page tree.
     */
    private static function count_pages( string $raw ): int {
        if ( preg_match( '/\/Count\s+(\d+)/', $raw, $m ) ) {
            return (int) $m[1];
        }
        return 1;
    }

    /**
     * Extract all raw content streams from the PDF binary.
     *
     * @return string[]
     */
    private static function extract_streams( string $raw ): array {
        $streams = [];
        $offset  = 0;

        while ( ( $start = strpos( $raw, 'stream', $offset ) ) !== false ) {
            // The byte after "stream" must be \r\n or \n.
            $after = substr( $raw, $start + 6, 2 );
            if ( $after[0] === "\r" && isset( $after[1] ) && $after[1] === "\n" ) {
                $data_start = $start + 8;
            } elseif ( $after[0] === "\n" ) {
                $data_start = $start + 7;
            } else {
                $offset = $start + 6;
                continue;
            }

            $end = strpos( $raw, 'endstream', $data_start );
            if ( false === $end ) {
                break;
            }

            $streams[] = substr( $raw, $data_start, $end - $data_start );
            $offset    = $end + 9;
        }

        return $streams;
    }

    /**
     * Extract human-readable text from a single content stream.
     *
     * Tries FlateDecode (gzip) first, then treats as plain text.
     * Parses PDF text operators: Tj, TJ, ', "
     *
     * @param string $stream Raw stream bytes.
     * @return string
     */
    private static function text_from_stream( string $stream ): string {
        // Try to decompress (FlateDecode).
        if ( function_exists( 'gzuncompress' ) ) {
            $decompressed = @gzuncompress( $stream );
            if ( false !== $decompressed ) {
                $stream = $decompressed;
            } else {
                // Try gzinflate (some PDFs omit the zlib header).
                $decompressed = @gzinflate( $stream );
                if ( false !== $decompressed ) {
                    $stream = $decompressed;
                }
            }
        }

        return self::parse_text_operators( $stream );
    }

    /**
     * Parse PDF content stream text operators and return plain text.
     *
     * Operators handled:
     *   Tj  — show string
     *   TJ  — show array of strings/kerning
     *   '   — move to next line and show string
     *   "   — set word/char spacing, move, show string
     *   Td/TD/T* — new line hints (add newline to output)
     *
     * @param string $stream Decoded stream content.
     * @return string
     */
    private static function parse_text_operators( string $stream ): string {
        $lines  = [];
        $buffer = '';

        // Work only inside BT...ET blocks (Begin Text / End Text).
        preg_match_all( '/BT(.*?)ET/s', $stream, $blocks );

        if ( empty( $blocks[1] ) ) {
            return '';
        }

        foreach ( $blocks[1] as $block ) {
            $block_text = '';

            // Tokenise the block.
            $pos = 0;
            $len = strlen( $block );

            while ( $pos < $len ) {
                // Skip whitespace.
                while ( $pos < $len && ctype_space( $block[ $pos ] ) ) {
                    $pos++;
                }
                if ( $pos >= $len ) {
                    break;
                }

                $ch = $block[ $pos ];

                // Literal string: (...)
                if ( $ch === '(' ) {
                    [ $str, $pos ] = self::read_literal_string( $block, $pos );
                    $buffer = $str;
                    continue;
                }

                // Hex string: <...>
                if ( $ch === '<' && isset( $block[ $pos + 1 ] ) && $block[ $pos + 1 ] !== '<' ) {
                    [ $str, $pos ] = self::read_hex_string( $block, $pos );
                    $buffer = $str;
                    continue;
                }

                // Array: [...]
                if ( $ch === '[' ) {
                    [ $arr_text, $pos ] = self::read_array_text( $block, $pos );
                    $buffer = $arr_text;
                    continue;
                }

                // Read operator/token.
                $token_start = $pos;
                while ( $pos < $len && ! ctype_space( $block[ $pos ] ) && $block[ $pos ] !== '(' && $block[ $pos ] !== '[' ) {
                    $pos++;
                }
                $token = substr( $block, $token_start, $pos - $token_start );

                switch ( $token ) {
                    case 'Tj':
                    case "'":
                    case '"':
                        if ( '' !== $buffer ) {
                            $block_text .= $buffer . ' ';
                            $buffer      = '';
                        }
                        if ( $token === "'" || $token === '"' ) {
                            $block_text .= "\n";
                        }
                        break;

                    case 'TJ':
                        if ( '' !== $buffer ) {
                            $block_text .= $buffer . ' ';
                            $buffer      = '';
                        }
                        break;

                    case 'Td':
                    case 'TD':
                    case 'T*':
                        $block_text .= "\n";
                        $buffer      = '';
                        break;

                    default:
                        // Numeric or other operand — discard buffer only if it
                        // looks like a number (not a text string we just read).
                        if ( is_numeric( $token ) || preg_match( '/^-?\d*\.?\d+$/', $token ) ) {
                            // numeric operand — keep buffer
                        } else {
                            $buffer = '';
                        }
                        break;
                }
            }

            $text = trim( $block_text );
            if ( '' !== $text ) {
                $lines[] = $text;
            }
        }

        return implode( "\n", $lines );
    }

    /**
     * Read a PDF literal string starting at $pos (the opening '(').
     * Handles nested parentheses and escape sequences.
     *
     * @return array{0: string, 1: int} [decoded string, new position]
     */
    private static function read_literal_string( string $data, int $pos ): array {
        $pos++;  // skip '('
        $result = '';
        $depth  = 1;
        $len    = strlen( $data );

        while ( $pos < $len && $depth > 0 ) {
            $ch = $data[ $pos ];

            if ( $ch === '\\' && $pos + 1 < $len ) {
                $next = $data[ $pos + 1 ];
                switch ( $next ) {
                    case 'n':  $result .= "\n"; break;
                    case 'r':  $result .= "\r"; break;
                    case 't':  $result .= "\t"; break;
                    case '(':  $result .= '(';  break;
                    case ')':  $result .= ')';  break;
                    case '\\': $result .= '\\'; break;
                    default:   $result .= $next; break;
                }
                $pos += 2;
                continue;
            }

            if ( $ch === '(' ) {
                $depth++;
            } elseif ( $ch === ')' ) {
                $depth--;
                if ( $depth === 0 ) {
                    $pos++;
                    break;
                }
            }

            if ( $depth > 0 ) {
                $result .= $ch;
            }
            $pos++;
        }

        // Strip non-printable characters except newline/tab.
        $result = preg_replace( '/[^\x09\x0A\x0D\x20-\x7E]/', '', $result );

        return [ $result, $pos ];
    }

    /**
     * Read a PDF hex string starting at $pos (the opening '<').
     *
     * @return array{0: string, 1: int}
     */
    private static function read_hex_string( string $data, int $pos ): array {
        $pos++;  // skip '<'
        $hex = '';
        $len = strlen( $data );

        while ( $pos < $len && $data[ $pos ] !== '>' ) {
            if ( ctype_xdigit( $data[ $pos ] ) ) {
                $hex .= $data[ $pos ];
            }
            $pos++;
        }
        $pos++;  // skip '>'

        if ( strlen( $hex ) % 2 !== 0 ) {
            $hex .= '0';
        }

        $result = '';
        for ( $i = 0; $i < strlen( $hex ); $i += 2 ) {
            $byte = hexdec( substr( $hex, $i, 2 ) );
            if ( $byte >= 0x20 && $byte <= 0x7E ) {
                $result .= chr( $byte );
            }
        }

        return [ $result, $pos ];
    }

    /**
     * Read a PDF array [...] and concatenate any string elements as text.
     *
     * @return array{0: string, 1: int}
     */
    private static function read_array_text( string $data, int $pos ): array {
        $pos++;  // skip '['
        $result = '';
        $len    = strlen( $data );

        while ( $pos < $len && $data[ $pos ] !== ']' ) {
            if ( ctype_space( $data[ $pos ] ) ) {
                $pos++;
                continue;
            }

            if ( $data[ $pos ] === '(' ) {
                [ $str, $pos ] = self::read_literal_string( $data, $pos );
                $result .= $str;
                continue;
            }

            if ( $data[ $pos ] === '<' && isset( $data[ $pos + 1 ] ) && $data[ $pos + 1 ] !== '<' ) {
                [ $str, $pos ] = self::read_hex_string( $data, $pos );
                $result .= $str;
                continue;
            }

            // Skip numbers (kerning values) and other tokens.
            while ( $pos < $len && ! ctype_space( $data[ $pos ] ) && $data[ $pos ] !== '(' && $data[ $pos ] !== '<' && $data[ $pos ] !== ']' ) {
                $pos++;
            }
        }

        $pos++;  // skip ']'
        return [ $result, $pos ];
    }
}
