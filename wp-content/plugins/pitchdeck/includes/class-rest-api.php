<?php
defined( 'ABSPATH' ) || exit;

class Pitchdeck_REST_API {

    const NAMESPACE = 'pitchdeck/v1';

    /**
     * Register REST routes. Called on 'rest_api_init'.
     */
    public static function register_routes(): void {
        register_rest_route( self::NAMESPACE, '/upload', [
            'methods'             => WP_REST_Server::CREATABLE,
            'callback'            => [ __CLASS__, 'handle_upload' ],
            'permission_callback' => [ __CLASS__, 'check_permissions' ],
        ] );

        register_rest_route( self::NAMESPACE, '/generate-script', [
            'methods'             => WP_REST_Server::CREATABLE,
            'callback'            => [ __CLASS__, 'handle_generate_script' ],
            'permission_callback' => [ __CLASS__, 'check_permissions' ],
            'args'                => [
                'job_id' => [
                    'required'          => true,
                    'type'              => 'string',
                    'sanitize_callback' => 'sanitize_text_field',
                ],
                'language' => [
                    'required'          => false,
                    'type'              => 'string',
                    'default'           => 'Finnish',
                    'sanitize_callback' => 'sanitize_text_field',
                ],
            ],
        ] );

        register_rest_route( self::NAMESPACE, '/save-slides', [
            'methods'             => WP_REST_Server::CREATABLE,
            'callback'            => [ __CLASS__, 'handle_save_slides' ],
            'permission_callback' => [ __CLASS__, 'check_permissions' ],
            'args'                => [
                'job_id' => [
                    'required'          => true,
                    'type'              => 'string',
                    'sanitize_callback' => 'sanitize_text_field',
                ],
                'slides' => [
                    'required' => true,
                    'type'     => 'array',
                ],
            ],
        ] );
    }

    /**
     * Permission check. WordPress verifies the X-WP-Nonce header automatically.
     * Returning true allows any request with a valid nonce.
     * TODO: restrict to logged-in users in production.
     */
    public static function check_permissions(): bool {
        return true;
    }

    /**
     * POST /wp-json/pitchdeck/v1/upload
     *
     * Accepts: multipart/form-data with field 'pptx_file'
     * Returns: { job_id: string, slides: SlideStruct[] }
     */
    public static function handle_upload( WP_REST_Request $request ) {
        $files = $request->get_file_params();

        if ( empty( $files['pptx_file'] ) || UPLOAD_ERR_OK !== $files['pptx_file']['error'] ) {
            return new WP_Error( 'no_file', 'No valid PPTX file was uploaded.', [ 'status' => 400 ] );
        }

        $file = $files['pptx_file'];

        // Validate extension.
        $ext = strtolower( pathinfo( $file['name'], PATHINFO_EXTENSION ) );
        if ( ! in_array( $ext, [ 'pptx', 'pdf' ], true ) ) {
            return new WP_Error( 'invalid_file_type', 'Only .pptx or .pdf files are accepted.', [ 'status' => 415 ] );
        }

        // Move to WP uploads/pitchdeck/.
        $upload_dir = wp_upload_dir();
        $dest_dir   = trailingslashit( $upload_dir['basedir'] ) . 'pitchdeck/';
        wp_mkdir_p( $dest_dir );

        $job_id = self::generate_uuid_v4();
        $dest   = $dest_dir . $job_id . '.' . $ext;

        if ( ! move_uploaded_file( $file['tmp_name'], $dest ) ) {
            return new WP_Error( 'upload_failed', 'Could not save the uploaded file.', [ 'status' => 500 ] );
        }

        // Give the parser more room for large files.
        set_time_limit( 120 );
        wp_raise_memory_limit( 'image' );

        // Parse the file.
        try {
            if ( 'pdf' === $ext ) {
                $slides = Pitchdeck_PDF_Parser::parse( $dest );
            } else {
                $slides = Pitchdeck_PPTX_Parser::parse( $dest );
            }
        } catch ( RuntimeException $e ) {
            @unlink( $dest );
            return new WP_Error( 'parse_failed', $e->getMessage(), [ 'status' => 422 ] );
        }

        return rest_ensure_response( [
            'job_id' => $job_id,
            'slides' => $slides,
        ] );
    }

    /**
     * POST /wp-json/pitchdeck/v1/save-slides
     *
     * Accepts: application/json { job_id: string, slides: SlideStruct[] }
     * Returns: { success: bool, saved_count: int }
     */
    public static function handle_save_slides( WP_REST_Request $request ) {
        $job_id = $request->get_param( 'job_id' );
        $slides = $request->get_param( 'slides' );

        if ( empty( $job_id ) || ! is_array( $slides ) || empty( $slides ) ) {
            return new WP_Error( 'invalid_data', 'job_id and a non-empty slides array are required.', [ 'status' => 400 ] );
        }

        foreach ( $slides as $i => $slide ) {
            if ( ! isset( $slide['slide_number'], $slide['slide_text'] ) ) {
                return new WP_Error(
                    'invalid_slide',
                    "Slide at index {$i} is missing slide_number or slide_text.",
                    [ 'status' => 400 ]
                );
            }
        }

        $success = Pitchdeck_DB::save_slides( $job_id, $slides );

        if ( ! $success ) {
            return new WP_Error( 'db_error', 'One or more slides could not be saved.', [ 'status' => 500 ] );
        }

        return rest_ensure_response( [
            'success'     => true,
            'saved_count' => count( $slides ),
        ] );
    }

    /**
     * POST /wp-json/pitchdeck/v1/generate-script
     *
     * Accepts: application/json { job_id: string }
     * Returns: { success: bool, scripts: [{slide_number, script_text}, ...] }
     */
    public static function handle_generate_script( WP_REST_Request $request ) {
        $job_id   = $request->get_param( 'job_id' );
        $language = $request->get_param( 'language' ) ?: 'Finnish';

        $slides = Pitchdeck_DB::get_slides_by_job( $job_id );

        if ( empty( $slides ) ) {
            return new WP_Error( 'no_slides', 'No slides found for this job. Save slides first.', [ 'status' => 404 ] );
        }

        try {
            set_time_limit( 120 );
            $scripts = Pitchdeck_OpenAI::generate_scripts( $slides, $language );
        } catch ( RuntimeException $e ) {
            return new WP_Error( 'openai_error', $e->getMessage(), [ 'status' => 502 ] );
        }

        Pitchdeck_DB::save_scripts( $job_id, $scripts );

        // Format for the frontend: array of {slide_number, script_text}.
        $output = [];
        foreach ( $scripts as $slide_number => $script_text ) {
            $output[] = [
                'slide_number' => $slide_number,
                'script_text'  => $script_text,
            ];
        }
        usort( $output, fn( $a, $b ) => $a['slide_number'] <=> $b['slide_number'] );

        return rest_ensure_response( [
            'success' => true,
            'scripts' => $output,
        ] );
    }

    /**
     * Generate a UUID v4 string using random_bytes().
     */
    private static function generate_uuid_v4(): string {
        $data    = random_bytes( 16 );
        $data[6] = chr( ord( $data[6] ) & 0x0f | 0x40 ); // version 4
        $data[8] = chr( ord( $data[8] ) & 0x3f | 0x80 ); // variant
        return vsprintf( '%s%s-%s-%s-%s-%s%s%s', str_split( bin2hex( $data ), 4 ) );
    }
}
