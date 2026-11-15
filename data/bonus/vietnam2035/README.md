# Vietnam 2035 bonus corpus

Source: *Việt Nam 2035: Hướng tới Thịnh vượng, Sáng tạo, Công bằng và Dân chủ*, World Bank and Vietnam Ministry of Planning and Investment, 2016, DOI 10.1596/978-1-4648-0824-1. Official Vietnamese PDF: <https://documents.worldbank.org/curated/en/462881491821948950/pdf/103435-v2-VIETNAMESE-PUBLIC-PUBDATE-11-30-2016.pdf>.

The PDF says it is licensed under Creative Commons Attribution 3.0 IGO. Required attribution: World Bank and Vietnam Ministry of Planning and Investment. 2016. *Vietnam 2035: Toward Prosperity, Creativity, Equity, and Democracy*. Washington, DC: World Bank. doi:10.1596/978-1-4648-0824-1. CC BY 3.0 IGO. The book's rights page warns that some third-party tables, charts, and images may be excluded; this repository therefore links to the official source rather than redistributing the PDF or visual crops. Verify individual visual rights before reuse.

`pages.jsonl` contains layout-preserving text extracted from each PDF physical page with Poppler. `index_manifest.json` records the source and index hashes, page counts, extraction method, and pages that yielded insufficient text. Page numbers are physical PDF page numbers (1-based); use those numbers in the official PDF viewer. This is a text index, not a claim of complete visual/OCR coverage.

Rebuild with Poppler (`pdftotext`, `pdfinfo`):

```sh
python3 scripts/index_vietnam2035.py /path/to/vietnam2035_vi.pdf
python3 scripts/inventory_vietnam2035.py /path/to/vietnam2035_vi.pdf
python3 scripts/search_vietnam2035.py 'câu hỏi'
```

The source PDF remains available from the linked official World Bank record.

`visual_inventory.jsonl` is an automatically detected list of figure and table
captions, not a complete inventory: the caption's physical page and figure number
are a locator, and neither detection nor visual contents have been audited.
`bitmap_inventory.jsonl` lists 304 bitmap and mask objects on 107 pages; bitmap
objects can include decorations and masks and do not include vector charts.
`skipped_pages_audit.json` documents manual review of the 11 pages omitted by
the text extractor (10 blank pages and the short title on page 3).
For an exploratory, local vision-model description (not verified evidence):

```sh
ollama pull qwen2.5vl:3b
python3 scripts/describe_vietnam2035.py /path/to/vietnam2035_vi.pdf --pages 118 --output results/bonus/pilot/visual.jsonl
.venv/bin/python scripts/bonus_pilot.py 'Câu hỏi' --visual-index results/bonus/pilot/visual.jsonl --output results/bonus/pilot/example.json
```

Images are rendered in a temporary directory and are not stored by this script.
The vision output may contain errors and must be compared with the original.
These scripts and the exploratory pilot are not a completed benchmark or a claim
that the 90% advanced-exercise requirement has been met.

An experimental image index can be generated without retaining the page images:

```sh
.venv/bin/python scripts/index_bonus_images.py /path/to/vietnam2035_vi.pdf --output /tmp/vietnam2035-clip-index
.venv/bin/python scripts/search_bonus_images.py 'biểu đồ sản lượng' --index /tmp/vietnam2035-clip-index
.venv/bin/python scripts/bonus_visual_agent.py 'Câu hỏi về hình' --pdf /path/to/vietnam2035_vi.pdf --image-index /tmp/vietnam2035-clip-index --output results/bonus/pilot/visual_agent.json
```

The image index has one full-page and four quadrant vectors per page with pixel
coordinates at a 1200-pixel render scale. The CLIP model and the vision model
are exploratory; low-resolution crops, Vietnamese-language queries, missing
text pages and vision hallucinations can all reduce accuracy. Similarity scores
and unverified model descriptions are not a substitute for checking the PDF.

`visual_verified.jsonl` contains manual descriptions of HÌNH 2.11, 4.6, 4.9 and
4.10, checked against their physical PDF pages. These four figures are not a complete
audit of the document's figures or an evaluation set. Use it with
`--visual-index data/bonus/vietnam2035/visual_verified.jsonl` for experimentation.
`visual_verified_v2.jsonl` adds checked descriptions of figures 4.18, 5.4, 5.5
and 5.10. The eight checked figures are still only a small subset of all visuals;
the CLIP coverage and the on-demand model do not prove that the remaining
figures can be answered accurately.
