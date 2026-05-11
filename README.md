# howtos

Dremel Lab how-to guides and operational documentation

## Available Guides

### [Getting Access to Dremel Lab S3 Files via Globus](guides/s3-globus-access/s3_globus_access_guide.md)
A step-by-step guide for Dremel Lab members to set up Globus access to the lab's S3 storage. Covers authentication via UVA NetBadge, finding collections, adding S3 credentials, and handling different storage classes.

**Time to complete:** 5-10 minutes  
**Prerequisites:** Active virginia.edu account

---

## Guide Directory Structure

Each guide has its own directory under `guides/`:

```
guides/
├── s3-globus-access/
│   ├── s3_globus_access_guide.md      (source markdown)
│   ├── s3_globus_access_guide.qmd     (Quarto document)
│   ├── s3_globus_access_guide.html    (rendered HTML)
│   ├── s3_globus_access_guide_files/  (generated assets)
│   └── images/                         (screenshots and diagrams)
```

## Contributing

To add a new how-to guide:
1. Create a new directory under `guides/` with a descriptive name (e.g., `guides/topic-name/`)
2. Create source files:
   - `topic_name.md` (markdown source)
   - `topic_name.qmd` (Quarto document with metadata)
   - `images/` subdirectory for screenshots
3. Follow the structure: Overview → Prerequisites → Step-by-Step → Troubleshooting → Key Points
4. Render with Quarto: `quarto render guides/topic-name/topic_name.qmd`
5. Update this README with a link to the new guide
