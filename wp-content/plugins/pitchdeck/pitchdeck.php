<?php
/**
 * Plugin Name: Pitchdeck
 * Description: Upload a PPTX, extract slide text, add notes per slide, generate voiceover scripts.
 * Version:     0.1.0
 * Author:      GR
 * Text Domain: pitchdeck
 */

defined( 'ABSPATH' ) || exit;

define( 'PITCHDECK_VERSION',    '0.1.0' );
define( 'PITCHDECK_PLUGIN_DIR', plugin_dir_path( __FILE__ ) );
define( 'PITCHDECK_PLUGIN_URL', plugin_dir_url( __FILE__ ) );

require_once PITCHDECK_PLUGIN_DIR . 'includes/class-db.php';
require_once PITCHDECK_PLUGIN_DIR . 'includes/class-pptx-parser.php';
require_once PITCHDECK_PLUGIN_DIR . 'includes/class-pdf-parser.php';
require_once PITCHDECK_PLUGIN_DIR . 'includes/class-rest-api.php';

// Create DB table on activation.
register_activation_hook( __FILE__, [ 'Pitchdeck_DB', 'create_table' ] );

// Boot REST API.
add_action( 'rest_api_init', [ 'Pitchdeck_REST_API', 'register_routes' ] );

// Register shortcode.
add_shortcode( 'pitchdeck', 'pitchdeck_shortcode_render' );

// Register assets (only enqueued when shortcode is on the page).
add_action( 'wp_enqueue_scripts', 'pitchdeck_register_assets' );

function pitchdeck_register_assets(): void {
    wp_register_script(
        'pitchdeck-js',
        PITCHDECK_PLUGIN_URL . 'assets/pitchdeck.js',
        [],
        PITCHDECK_VERSION,
        true
    );
    wp_localize_script( 'pitchdeck-js', 'pitchdeck_config', [
        'rest_url' => esc_url_raw( rest_url( 'pitchdeck/v1' ) ),
        'nonce'    => wp_create_nonce( 'wp_rest' ),
    ] );
    wp_register_style(
        'pitchdeck-css',
        PITCHDECK_PLUGIN_URL . 'assets/pitchdeck.css',
        [],
        PITCHDECK_VERSION
    );
}

function pitchdeck_shortcode_render( array $atts ): string {
    wp_enqueue_script( 'pitchdeck-js' );
    wp_enqueue_style( 'pitchdeck-css' );

    ob_start();
    ?>
    <div id="pitchdeck-app">
        <form id="pitchdeck-upload-form" enctype="multipart/form-data">
            <label for="pitchdeck-file">Upload your PPTX or PDF file:</label>
            <input type="file" id="pitchdeck-file" name="pptx_file" accept=".pptx,.pdf" required />
            <button type="submit">Extract Slides</button>
        </form>
        <div id="pitchdeck-status"></div>
        <div id="pitchdeck-slides-container"></div>
        <div id="pitchdeck-save-section" style="display:none;">
            <button id="pitchdeck-save-btn">Save Slide Notes</button>
        </div>
    </div>
    <?php
    return ob_get_clean();
}
