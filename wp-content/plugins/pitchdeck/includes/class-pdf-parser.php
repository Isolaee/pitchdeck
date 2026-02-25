<?php
defined( 'ABSPATH' ) || exit;

/**
 * Parses a .pdf file and extracts text per page as slides.
 *
 * Uses the `pdftotext` CLI tool (poppler-utils) if available on the server.
 * Each PDF page becomes one "slide".
 */
class Pitchdeck_PDF_Parser {

    /**
     * Parse a .pdf file and return an array of slide data structs.
     *
     * Each struct:
     *   [
     *     'slide_number' => int,
     *     'slide_text'   => string,
     *     'extra_info'   => string,
     *   ]
     *
     * @param string $file_path Absolute path to the .pdf file.
     * @return array
     * @throws RuntimeException If pdftotext is unavailable or parsing fails.
     */
    public static function parse( string $file_path ): array {
        if ( ! file_exists( $file_path ) ) {
            throw new RuntimeException( "PDF file not found: {$file_path}" );
        }

        // Use pdftotext (poppler-utils) to extract text with form feed between pages.
        $escaped = escapeshellarg( $file_path );
        $output  = shell_exec( "pdftotext -layout {$escaped} -" );

        if ( null === $output || '' === $output ) {
            throw new RuntimeException(
                'Could not extract text from PDF. Ensure pdftotext (poppler-utils) is installed on the server.'
            );
        }

        // pdftotext separates pages with form feed character (\f = chr(12)).
        $pages  = explode( "\f", $output );
        $slides = [];

        foreach ( $pages as $index => $page_text ) {
            $text = trim( $page_text );
            // Skip empty trailing pages (pdftotext often adds a trailing \f).
            if ( '' === $text ) {
                continue;
            }
            $slides[] = [
                'slide_number' => count( $slides ) + 1,
                'slide_text'   => $text,
                'extra_info'   => '',
            ];
        }

        if ( empty( $slides ) ) {
            throw new RuntimeException( 'No text content found in the PDF.' );
        }

        return $slides;
    }
}
