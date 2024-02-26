# Kobo Progress Screensaver

## Description
This is a simple python script that generates a screensaver for Kobo e-readers. It displays the covers of all the books
you have read this year in a nice grid view.<br>
The script automatically detects the location of your connected Kobo e-reader, collects your read books from the
database and the book covers from the device.<br>
It then generates the screensaver as a png-file in the Kobo's screensaver folder.

## Example image
<img src="2024Progress.png" alt="">

## Usage
``python kobo_progress_screensaver.py`` <br>
That's it. The script will do the rest. Otherwise, it will tell you what went wrong and you can complain 
in an issue about it to me.

//TODO: Add an Exe-File for Windows users

## Configuration
The script has a few configuration options that can be set in the script itself. <br>
Probably the most interesting one is the screen size of your Kobo.<br> 
The script assumes a Kobo Clara 2e, and it should
still work with other models. If not, you can adjust the screen size in the `get_kobo_screen_size` function.
