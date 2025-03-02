# Mass Music Downloader

Super hacky python mass music downloader with a super hacky way to setup

## Usage
Run by using `python downloader.py -f [Song List]`
You can also use the -o flag to specify the output directory. (Default is set to the user's music directory)
If the output directory does not exist, the program will create it.

Example for using the -o flag:
`python downloader.py -f [Song List] -o [Output Directory]`

## `download.conf`
This holds the commands for yt-dlp and khinsider.py

Format:

```
[yt-dlp]
{INSERT YOUR COMMAND FOR VIDEOS}
{INSERT YOUR COMMAND FOR PLAYLISTS/ALBUMS}

[khinsider]
{INSERT YOUR COMMAND}
```

* Do note that the command must be written in full (eg. `yt-dlp` -f "bestaudio")
* Additionally the program will inject the `--no-config` flag which will ignore any existing yt-dlp configuration files

## `Song-List.conf`
Name this however you want, just make sure to include the file by calling the program with `-f [Filename]`. This holds all the songs you want to download.

Format:
```
# [Category]
[Index] | [Name] [Link]

```

Where:
Category -> Parent Folder where being under nothing means there will not be a parent folder
Name -> The name you want for the song downloaded
Link -> A youtube or khinsider link. If it is not any of those then the program will open the link on your web browser

These are specific categories that result in certain behaviour:
1. "`#  / # Root`": Empty category names are placed directly in the output directory
2. "`# Khinsider`": Same as "`# `" and indicates that this is a khinsider link. This should be reserved for khinsider links only.
3. "`# Album / # Albums`": Same as "`# `" and indicates the yt-dlp downloader to use your configured command for playlists. This should be reserved for youtube links only.

* Note that anything that does not start with "#" or a number is ignored

## Dependencies
1. [yt-dlp](https://github.com/yt-dlp/yt-dlp)
2. [khinsider mass downloader](https://github.com/obskyr/khinsider)

and all of their dependencies

## Example .conf files

`backup.conf`:

```
[yt-dlp]
yt-dlp -o "%(title)s.%(ext)s" --format "bestaudio" --remux-video "webm>opus/aac>m4a" --embed-thumbnail
yt-dlp -o "%(playlist_index)s-%(title)s.%(ext)s" --format "bestaudio" --remux-video "webm>opus/aac>m4a" --embed-thumbnail

[khinsider]
python khinsider.py --format flac
```

`Song-List.conf`:

```
# Khinsider     // These will be downloaded as "~/Music/[Name]"
1  | "The Great Ace Attorney: Adventures Grand Performance Recording" https://downloads.khinsider.com/game-soundtracks/album/the-great-ace-attorney-adventures-grand-performance-recording
2  | "The Great Ace Attorney 2: Resolve Grand Performance Recording" https://downloads.khinsider.com/game-soundtracks/album/dai-gyakuten-saiban-2-naruhodou-ryuunosuke-no-kakugo-gekiban-ongaku-daizenshuu-2017

1  | "MarbleBlue." https://www.youtube.com/watch?v=ifScxTIozhg      // This will be placed in "~/Music"

# Chinese   // These will be placed in "~/Music/Chinese"
1  | "怎么了" https://www.youtube.com/watch?v=KFxO-Mj3q0c
2  | "一样美丽" https://www.youtube.com/watch?v=-_itKmjEq18
3  | "爱我的时候" https://www.youtube.com/watch?v=K2ZDHgTLEVQ


Khinsider Mass Downloader               // This line is ignored
https://github.com/obskyr/khinsider     // This line is ignored
```