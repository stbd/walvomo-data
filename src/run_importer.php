<?php
require_once('importer.php');

$runner = new importer();

if (isset($argv[1])) {
   $runner->setDirectory($argv[1]);
}

if (isset($argv[2])) {
   $runner->setFilter($argv[2]);
}

$runner->import();
