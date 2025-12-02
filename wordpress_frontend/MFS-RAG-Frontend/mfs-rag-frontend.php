<?php
/*
Plugin Name: MFS Rag Frontend
Description: Frontend for the Manoa Faculty Senate RAG System. Use Shortcode [mfs_rag_frontend]
Version: 1.01
Author: Kyle Bueche

Shortcode: [mfs_rag_frontend]
*/

if (!defined('ABSPATH')) exit;

/*
Injects HTML & CSS into the shortcode: [mfs_rag_frontend].
Runs JavaScript code once all the HTML has been loaded.
*/
function rag_frontend( $atts ) {
    load_js_from_file();
    load_css_from_file();
    return load_html_from_file();
}

/*
Load the JavaScript.
Function form:
wp_enqueue_script(handle, src, deps, ver, args[strategy, in_footer])
*/
function load_js_from_file() {
    wp_enqueue_script(
        'mfs-rag-frontend-script',
        plugins_url( 'mfs-rag-frontend.js', __FILE__ ),
        array(),
        '1.0.0',
        array(
            'strategy' => 'defer', // Only run once DOM tree has fully loaded
            'in_footer' => false
        )
    );
}

/*
Load the CSS stylesheet.
Function form:
wp_enqueue_script(handle, src, deps, ver, media)
*/
function load_css_from_file() {
    wp_enqueue_style(
        'mfs-rag-frontend-style',
        plugins_url( 'mfs-rag-frontend.css', __FILE__ ),
        array(),
        '1.0.0',
        'all' // Defined for all media types
    );
}

/*
Parses HTML from file, and returns it as what the shortcode expects.
*/
function load_html_from_file() {
    ob_start();
    include( 'mfs-rag-frontend.html' );
    $html_content = ob_get_clean();
    return $html_content;
}

// Register the shortcode
add_shortcode( 'mfs_rag_frontend', 'rag_frontend' );
