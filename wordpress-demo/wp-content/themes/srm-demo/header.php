<?php
/**
 * Header template. Kept intentionally minimal — this theme exists to
 * demonstrate chatbot embedding, not to be a production SRM-SM theme.
 */
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<header class="site-header">
    <a class="site-logo" href="<?php echo esc_url( home_url( '/' ) ); ?>">SRM<span>-SM</span></a>
    <nav class="site-nav">
        <a href="<?php echo esc_url( home_url( '/' ) ); ?>">Accueil</a>
        <a href="#services">Nos services</a>
        <a href="#agences">Agences</a>
        <a href="#contact">Contact</a>
    </nav>
</header>
