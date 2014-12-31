<?php

class Importer
{

    const DEFAULT_DIRECTORY = "../data/";
    private $_directory;
    private $_filter;

    public function __construct($directory = self::DEFAULT_DIRECTORY) {
    	$this->_directory = $directory;
    }

    public function setFilter($filter) {
        $this->_filter = $filter;
    }

    public function setDirectory($directory) {
    	$this->_directory = $directory;
    }

    public function import()
    {
	$cb = new Couchbase("127.0.0.1:8091");
        $files = scandir($this->_directory);
	foreach ($files as $filename) {
	    $pathInfo = pathinfo($filename);
	    if (strpos($pathInfo['filename'], 'data_') !== 0 || $pathInfo['extension'] !== 'bin') {
	       continue;
	    }
            if (isset($this->_filter) && !preg_match($this->_filter, $pathInfo['filename'])) {
               continue;
            }
	    if (filesize($this->_directory . $filename) != 0) {
	        $handle = fopen($this->_directory . $filename, "r");
            	$contents = fread($handle, filesize($this->_directory . $filename));
		$key = substr($pathInfo['filename'], 5);
		$cb->set($key, $contents);
	   }
	}
    }
}
