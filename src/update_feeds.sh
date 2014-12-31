python rssReader.py --log warn --update
php run_importer.php ../data/ /UpdateItem/
php run_importer.php ../data/ /Collection/
rm -f ../data/data_UpdateItem*.bin
rm -f ../data/data_Collection*