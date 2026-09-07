# Instagram DM Archive Viewer

A lightweight Python tool that converts an exported Instagram DM inbox into a standalone HTML viewer with an Instagram-inspired interface.

The project reads Instagram message export files and generates a single HTML file that can be opened directly in a web browser without running a server.

> **Status:** Work in Progress  
> The project is functional but still under development. More features, compatibility improvements, and UI refinements are planned.

## Features

- Convert Instagram DM exports into an HTML viewer
- Display multiple conversations
- Instagram-inspired dark UI
- Conversation sidebar
- Text messages
- Photos and image preview
- Videos
- Audio messages
- Stickers
- Shared links
- Video call messages
- Message reactions
- Group conversation sender names
- Message timestamps
- Date separators
- Automatic conversation previews
- Image lightbox
- Responsive layout
- Fully offline output
- No database or web server required

The current implementation processes `message_*.json` files from Instagram's exported inbox structure and combines multiple message files belonging to the same conversation.

## Requirements

- Python 3.8+
- An Instagram data export containing your messages
- A modern web browser

The current version uses only Python standard-library modules, so no external Python packages are required.

## Installation

Clone the repository:

```bash
git clone https://github.com/adityaksx/InstaDM-Viewer.git
cd instagram-dm-archive-viewer
```

No package installation is currently required.

## Instagram Export Structure

The tool expects an inbox structure similar to:

```text
messages/
└── inbox/
    ├── username_123456/
    │   ├── message_1.json
    │   ├── message_2.json
    │   └── photos/
    │       └── ...
    └── another_conversation/
        └── message_1.json
```

This structure corresponds to the expected folder layout implemented by the current program.

## Usage

### Basic

```bash
python dm_viewer.py
```

By default, the program looks for:

```text
messages/inbox
```

and generates:

```text
instagram_dms.html
```

### Specify the inbox

```bash
python dm_viewer.py --inbox messages/inbox
```

### Specify your username

```bash
python dm_viewer.py --inbox messages/inbox --me YourUsername
```

Your messages will be displayed on the right side of the conversation.

### Specify an output file

```bash
python dm_viewer.py \
    --inbox messages/inbox \
    --me YourUsername \
    --output dms.html
```

The available command-line arguments are `--inbox`, `--me`, and `--output`.

## Output

The program generates a self-contained HTML file containing the conversation data and viewer interface.

Example:

```text
messages/
└── inbox/
    └── ...

dm_viewer.py
instagram_dms.html
```

Open the generated HTML file directly in a browser:

```text
instagram_dms.html
```

The current implementation is designed to work offline after generation.

## Supported Message Types

The current implementation handles:

| Type | Support |
|---|---|
| Text | Yes |
| Photos | Yes |
| Videos | Yes |
| Audio | Yes |
| Stickers | Yes |
| Shared links | Yes |
| Reactions | Yes |
| Calls | Yes |
| Group messages | Yes |

Media files are embedded into the generated HTML using Base64 data URLs, allowing the resulting viewer to operate as a standalone file.

## Project Structure

```text
.
├── dm_viewer.py
├── README.md
├── requirements.txt
└── messages/
    └── inbox/
```

## Current Limitations

This project is still being improved.

Some current limitations include:

- Large exports can produce very large HTML files.
- Media is embedded directly into the HTML.
- The search interface is currently primarily UI rather than a complete conversation search system.
- The generated viewer does not reproduce every Instagram feature.
- Instagram export formats may change over time.
- Some media or message types may not be fully supported.
- Profile pictures and some metadata are not currently represented.

## Planned Improvements

Possible future improvements:

- [ ] Proper message search
- [ ] Conversation filtering
- [ ] Date-based message navigation
- [ ] Better media handling
- [ ] Profile pictures
- [ ] Message metadata viewer
- [ ] Export statistics
- [ ] Conversation/message counts
- [ ] Media gallery
- [ ] Better mobile interface
- [ ] Improved Instagram export compatibility
- [ ] Dark/light themes
- [ ] Faster loading for large exports
- [ ] Optional non-embedded media mode
- [ ] Better error handling
- [ ] Automatic export structure detection

## Privacy

This tool is intended for processing your own Instagram data locally.

The generated viewer contains your exported messages and media, so treat the generated HTML file as private data.

Do not upload generated archives containing personal conversations to public repositories.

## Disclaimer

This project is an independent, unofficial tool and is not affiliated with, endorsed by, or sponsored by Instagram or Meta.

Instagram is a trademark of Meta Platforms, Inc.

## Contributing

Contributions and improvements are welcome.

If you find a bug or have an idea for improving the viewer, open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
