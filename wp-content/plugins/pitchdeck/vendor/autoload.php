<?php

// Pitchdeck vendor autoloader — replaces composer-generated autoload.php
// Loads smalot/pdfparser (PSR-0) and symfony/polyfill-mbstring (PSR-4 + bootstrap file)

require_once __DIR__ . '/composer/ClassLoader.php';

$loader = new \Composer\Autoload\ClassLoader();

// PSR-0: smalot/pdfparser
// For PSR-0, $path is the base dir that already contains the namespace folder structure.
// e.g. path = vendor/smalot/pdfparser/src, class Smalot\PdfParser\Parser
//   => src/Smalot/PdfParser/Parser.php  ✓
$namespaces = require __DIR__ . '/composer/autoload_namespaces.php';
foreach ($namespaces as $namespace => $paths) {
    foreach ((array) $paths as $path) {
        $loader->add($namespace, $path);
    }
}

// PSR-4: symfony/polyfill-mbstring
$psr4 = require __DIR__ . '/composer/autoload_psr4.php';
foreach ($psr4 as $namespace => $paths) {
    foreach ((array) $paths as $path) {
        $loader->addPsr4($namespace, $path);
    }
}

$loader->register(true);

// Files (bootstrap includes)
$files = require __DIR__ . '/composer/autoload_files.php';
foreach ($files as $file) {
    if (file_exists($file)) {
        require_once $file;
    }
}

return $loader;
