"""Collect public YouTube titles and links, then generate the channel directory."""
import csv
import io
import json
import re
from collections import Counter
from pathlib import Path

import yt_dlp

ROOT = Path(__file__).resolve().parents[1]


def escape(text):
    text = " ".join(str(text).split())
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]").replace("<", "&lt;").replace(">", "&gt;")


def normalize(channel, raw):
    if raw.get("channel_id") != channel["channel_id"]:
        raise ValueError("YouTube returned a different channel")
    videos = []
    seen = set()
    tabs = raw.get("entries", [])
    if tabs and all(entry and entry.get("_type") != "playlist" for entry in tabs):
        tabs = [raw]
    for tab in tabs:
        if not tab or tab.get("_type") != "playlist":
            raise ValueError("Incomplete channel response")
        kind = tab["title"].rsplit(" - ", 1)[-1]
        entries = list(tab.get("entries") or [])
        for entry in entries:
            if not entry:
                raise ValueError("Missing video record")
            video_id = entry.get("id", "")
            title = entry.get("title", "")
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id) or not title:
                raise ValueError("Invalid video record")
            if video_id in seen:
                continue
            seen.add(video_id)
            videos.append({
                "id": video_id,
                "title": title,
                "url": "https://www.youtube.com/watch?v=" + video_id,
                "type": kind,
                "channel": channel["name"],
                "handle": channel["handle"],
            })
    if not videos:
        raise ValueError("YouTube returned no public uploads. Existing files preserved.")
    return videos


def generate(channels, records):
    outputs = {}
    all_videos = []
    overview = [
        "# YouTube Marketing", "",
        "A directory of public video titles and direct YouTube links for managed channels.", "",
        "Open a channel below to browse its uploads. Use Ctrl+F to find a title, or download the CSV to sort and search in Excel.", "",
        "| Channel | Public uploads | Browse | Export |",
        "| --- | ---: | --- | --- |",
    ]
    for channel, videos in zip(channels, records):
        handle = channel["handle"]
        all_videos.extend(videos)
        counts = Counter(video["type"] for video in videos)
        overview.append(f"| [{escape(channel['name'])}](https://www.youtube.com/@{handle}) | {len(videos)} | [Titles & links](channels/{handle}.md) | [CSV](data/{handle}.csv) |")
        lines = [
            f"# {escape(channel['name'])}", "",
            f"[YouTube channel](https://www.youtube.com/@{handle}) · [All channels](../README.md) · [Download CSV](../data/{handle}.csv)", "",
            f"**{len(videos)} public uploads** · " + " · ".join(f"{count} {kind}" for kind, count in counts.items()), "",
            "Browse by type below. Within each type, YouTube's channel order is preserved. Use Ctrl+F to find a title.", "",
        ]
        for kind in counts:
            lines.extend([f"## {escape(kind)}", "", "| Title | Link |", "| --- | --- |"])
            for video in videos:
                if video["type"] == kind:
                    lines.append(f"| {escape(video['title'])} | [Watch]({video['url']}) |")
            lines.append("")
        lines.extend(["---", "", "This list reflects the channel's public upload tabs. Private, unlisted and removed videos are outside the public listing.", ""])
        outputs[f"channels/{handle}.md"] = "\n".join(lines)
        csv_buffer = io.StringIO(newline="")
        writer = csv.DictWriter(csv_buffer, fieldnames=["type", "title", "url", "id"])
        writer.writeheader()
        for video in videos:
            row = {key: video[key] for key in writer.fieldnames}
            if row["title"].lstrip().startswith(("=", "+", "-", "@")):
                row["title"] = "'" + row["title"]
            writer.writerow(row)
        outputs[f"data/{handle}.csv"] = "\ufeff" + csv_buffer.getvalue()
    overview.extend([
        "", "## Automatic updates", "",
        "GitHub Actions refreshes all configured channels daily at 08:41 Pakistan time, and can also be run from Actions → Refresh YouTube channels → Run workflow.", "",
        "New uploads and edited titles are included on the next successful refresh. The workflow checks all public channel tabs using yt-dlp, without downloading video files. YouTube availability and access restrictions can affect refreshes. Check Actions if a run fails.", "",
        "## Add another channel", "",
        "Add its handle, channel ID and display name to channels.json. The next workflow run generates its separate list and CSV automatically.", "",
        "Schedules may be delayed by GitHub. Inactive public repositories can have scheduled workflows disabled after 60 days. Re-enable the workflow in Actions when needed.", "",
    ])
    outputs["README.md"] = "\n".join(overview)
    outputs["data/videos.json"] = json.dumps(all_videos, ensure_ascii=False, indent=2) + "\n"
    return outputs


def main():
    channels = json.loads((ROOT / "channels.json").read_text())
    handles = [channel["handle"] for channel in channels]
    if not channels or len(handles) != len(set(handles)):
        raise ValueError("Channel handles must be unique")
    records = []
    options = {
        "extract_flat": True, "skip_download": True, "quiet": True,
        "ignoreerrors": False, "socket_timeout": 30, "extractor_retries": 2,
    }
    with yt_dlp.YoutubeDL(options) as client:
        for channel in channels:
            if not re.fullmatch(r"[A-Za-z0-9_-]+", channel["handle"]):
                raise ValueError("Invalid channel handle")
            if not re.fullmatch(r"UC[A-Za-z0-9_-]{22}", channel["channel_id"]):
                raise ValueError("Invalid channel ID")
            url = "https://www.youtube.com/channel/" + channel["channel_id"]
            raw = client.extract_info(url, download=False)
            records.append(normalize(channel, raw))
    # Finish every channel before replacing any catalogue files.
    outputs = generate(channels, records)
    for path, content in outputs.items():
        destination = ROOT / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(destination)
    print(f"Refreshed {len(channels)} channel(s), {sum(map(len, records))} public uploads.")


if __name__ == "__main__":
    main()
