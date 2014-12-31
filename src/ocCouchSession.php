
<?php

$cmd = $argv[1];
$key = $argv[2];
$cb = new Couchbase("127.0.0.1:8091");

if ($cmd == "read") {
   echo "Reading key: $key\n";
   var_dump($cb->get($key));
   echo "\n";
} elseif ($cmd == "delete") {
  var_dump($cb->delete($key));
  echo "\n";
} else {
  echo "Invalid arguments\n";
  exit;
}

?>