<?php
/**
 * SRM-SM Demo theme setup.
 *
 * This theme exists to demonstrate that the SRM-SM RAG chatbot (a separate
 * Streamlit app) can be embedded into a WordPress site as a floating widget.
 * It is intentionally minimal.
 */

add_theme_support( 'title-tag' );
add_theme_support( 'post-thumbnails' );

/**
 * URL of the running Streamlit chatbot app. Change this if the app is
 * served from a different host/port than the local default.
 */
if ( ! defined( 'SRM_CHATBOT_URL' ) ) {
    define( 'SRM_CHATBOT_URL', 'http://localhost:8501' );
}

function srm_demo_enqueue_assets() {
    $theme_uri = get_stylesheet_directory_uri();
    $theme_dir = get_stylesheet_directory();

    wp_enqueue_style(
        'srm-demo-style',
        $theme_uri . '/style.css',
        array(),
        filemtime( $theme_dir . '/style.css' )
    );

    wp_enqueue_style(
        'srm-chat-widget',
        $theme_uri . '/assets/chat-widget.css',
        array(),
        filemtime( $theme_dir . '/assets/chat-widget.css' )
    );

    wp_enqueue_script(
        'srm-chat-widget',
        $theme_uri . '/assets/chat-widget.js',
        array(),
        filemtime( $theme_dir . '/assets/chat-widget.js' ),
        true
    );

    wp_localize_script( 'srm-chat-widget', 'srmChatbotConfig', array(
        'url' => SRM_CHATBOT_URL,
    ) );
}
add_action( 'wp_enqueue_scripts', 'srm_demo_enqueue_assets' );

/**
 * Prints the floating button + slide-out iframe panel markup. Runs on
 * wp_footer so it's available site-wide regardless of template.
 */
function srm_demo_render_chat_widget() {
    ?>
    <button id="srm-chat-toggle" type="button" aria-label="Ouvrir l'assistant SRM-SM" aria-expanded="false">
        <span class="srm-chat-toggle-icon-open">💬</span>
        <span class="srm-chat-toggle-icon-close">✕</span>
    </button>

    <div id="srm-chat-panel" hidden>
        <div id="srm-chat-panel-header">
            <span>💧 Assistant SRM-SM</span>
            <button id="srm-chat-panel-close" type="button" aria-label="Fermer l'assistant">✕</button>
        </div>
        <iframe
            id="srm-chat-iframe"
            title="Assistant virtuel SRM-SM"
            src="about:blank"
            data-src="<?php echo esc_url( SRM_CHATBOT_URL ); ?>"
            loading="lazy"
        ></iframe>
    </div>
    <?php
}
add_action( 'wp_footer', 'srm_demo_render_chat_widget' );
