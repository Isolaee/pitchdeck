<?php

/*
 * Minimal PSR-0 / PSR-4 class loader for the pitchdeck vendor directory.
 * Replaces the Composer-generated ClassLoader for cases where Composer
 * is not available on the deployment machine.
 */

namespace Composer\Autoload;

class ClassLoader
{
    private $prefixesPsr0  = [];
    private $prefixDirsPsr4 = [];
    private $fallbackDirs  = [];

    public function addPsr4($prefix, $path)
    {
        $this->prefixDirsPsr4[$prefix][] = rtrim($path, '/\\');
    }

    public function add($prefix, $path)
    {
        $this->prefixesPsr0[$prefix][] = rtrim($path, '/\\');
    }

    public function register($prepend = false)
    {
        spl_autoload_register([$this, 'loadClass'], true, $prepend);
    }

    public function loadClass($class)
    {
        // PSR-4
        foreach ($this->prefixDirsPsr4 as $prefix => $dirs) {
            if (strpos($class, $prefix) === 0) {
                $relative = substr($class, strlen($prefix));
                $relative = str_replace('\\', DIRECTORY_SEPARATOR, $relative);
                foreach ($dirs as $dir) {
                    $file = $dir . DIRECTORY_SEPARATOR . $relative . '.php';
                    if (file_exists($file)) {
                        require $file;
                        return true;
                    }
                }
            }
        }

        // PSR-0
        foreach ($this->prefixesPsr0 as $prefix => $dirs) {
            if (strpos($class, $prefix) === 0) {
                $relative = str_replace(['\\', '_'], DIRECTORY_SEPARATOR, $class);
                foreach ($dirs as $dir) {
                    $file = $dir . DIRECTORY_SEPARATOR . $relative . '.php';
                    if (file_exists($file)) {
                        require $file;
                        return true;
                    }
                }
            }
        }

        return false;
    }
}
