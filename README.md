# YouTube Marketing

A directory of public video titles and direct YouTube links for managed channels.

Open a channel below to browse its uploads. Use Ctrl+F to find a title, or download the CSV to sort and search in Excel.

| Channel | Public uploads | Browse | Export |
| --- | ---: | --- | --- |
| [MR MILU](https://www.youtube.com/@mistarmilu) | 24 | [Titles & links](channels/mistarmilu.md) | [CSV](data/mistarmilu.csv) |

## Automatic updates

GitHub Actions refreshes all configured channels daily at 08:41 Pakistan time, and can also be run from Actions → Refresh YouTube channels → Run workflow.

New uploads and edited titles are included on the next successful refresh. The workflow checks all public channel tabs using yt-dlp, without downloading video files. YouTube availability and access restrictions can affect refreshes. Check Actions if a run fails.

## Add another channel

Add its handle, channel ID and display name to channels.json. The next workflow run generates its separate list and CSV automatically.

Schedules may be delayed by GitHub. Inactive public repositories can have scheduled workflows disabled after 60 days. Re-enable the workflow in Actions when needed.
