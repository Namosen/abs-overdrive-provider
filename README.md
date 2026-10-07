# abs-overdrive-provider

A custom metadata provider for [Audiobookshelf](https://audiobookshelf.org) that searches the OverDrive/Libby catalog for audiobook metadata — title, author, narrator, series, cover, description, and more.

Uses the OverDrive Thunder API (the same API that powers the Libby app) via one or more public library catalogs. No OverDrive account, API key, or library card required.

---

## Quick Start

### 1. Add to your Audiobookshelf Docker Compose stack

```yaml
services:
  audiobookshelf:
    image: ghcr.io/advplyr/audiobookshelf:latest
    # ... your existing ABS config ...

  abs-overdrive-provider:
    image: ghcr.io/YOUR_GITHUB_USERNAME/abs-overdrive-provider:latest
    container_name: abs-overdrive-provider
    restart: unless-stopped
    ports:
      - "3847:3847"
    environment:
      - AUTH_TOKEN=your_secret_token_here
      - LIBRARY_KEYS=nypl,londonlibraries,tlc
```

### 2. Generate a token

```bash
openssl rand -hex 32
```

### 3. Add to Audiobookshelf

1. Go to **Settings → Item Metadata Tools → Custom Metadata Providers**
2. Click **Add**
3. Set:
   - **Name**: `OverDrive`
   - **URL**: `http://<your-server-ip>:3847`
   - **Authorization Header Value**: the value you set for `AUTH_TOKEN`

### 4. Use it

Open any book in ABS, click **Match**, and select **OverDrive** from the provider dropdown.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `AUTH_TOKEN` | *(empty)* | Secret token ABS sends with every request. Set something strong. |
| `LIBRARY_KEYS` | `nypl,londonlibraries,tlc` | Comma-separated OverDrive library slugs. Searched in parallel; results are deduplicated. |
| `PORT` | `3847` | Port the provider listens on. |

---

## Choosing Library Slugs

The slug is the short identifier from a library's Libby URL. For example, `libbyapp.com/library/nypl` → slug is `nypl`.

Find your own library's slug by visiting [libbyapp.com](https://libbyapp.com) and checking the URL after `/library/`, or by looking at any Libby share link (e.g. `share.libbyapp.com/title/123#library-SLUG`).

### Verified slugs

The following slugs have been verified against the OverDrive API.

#### United States
| Library | Slug |
|---|---|
| New York Public Library | `nypl` |
| Los Angeles Public Library | `lapl` |
| Chicago Public Library | `chipublib` |
| Boston Public Library | `bpl` |
| Seattle Public Library | `spl` |
| San Francisco Public Library | `sfpl` |
| Denver Public Library | `denver` |
| Miami-Dade Public Library | `mdpls` |
| Houston Public Library | `houstonlibrary` |
| Dallas Public Library | `dallaslibrary` |
| Phoenix Public Library | `phoenix` |
| San Diego Public Library | `sandiego` |
| Hennepin County Library (MN) | `hclib` |
| DC Public Library | `dcpl` |

#### United Kingdom
| Library | Slug |
|---|---|
| London Libraries Consortium | `londonlibraries` |
| The Libraries Consortium | `tlc` |

#### Canada
| Library | Slug |
|---|---|
| Toronto Public Library | `torontopubliclibrary` |
| Vancouver Public Library | `vpl` |
| Ottawa Public Library | `ottawalibrary` |

#### Australia
| Library | Slug |
|---|---|
| Queensland Libraries | `queensland` |

> **Tip:** The default `nypl,londonlibraries,tlc` covers the majority of English-language audiobooks. Add your local library's slug for the best regional coverage.

> **Note:** Slugs are not officially documented by OverDrive and may change. If a slug stops working, check your library's Libby URL for the current value.

---

## Standalone Deployment

If you prefer to run this outside of your ABS stack:

```bash
git clone https://github.com/Namosen/abs-overdrive-provider
cd abs-overdrive-provider
cp .env.example .env
# Edit .env and set your AUTH_TOKEN
docker compose up -d
```

---

## How It Works

1. ABS sends a `GET /search?query=<title>&author=<author>` request with your token in the `AUTHORIZATION` header.
2. The provider searches each configured library's OverDrive catalog in parallel via the Thunder API.
3. Results are deduplicated by OverDrive title ID and returned in ABS's expected format.

Because each library only carries a subset of OverDrive's full catalog, using multiple libraries across regions dramatically increases coverage. The default set of `nypl,londonlibraries,tlc` covers the majority of English-language audiobooks.

---

## Notes

- The Thunder API is unofficial and undocumented. It may break if OverDrive changes their infrastructure.
- Only audiobook-format results are returned.
- Rate limiting: searching 3 libraries concurrently per request is well within safe limits.

---

## Contributing

PRs welcome, especially for additional verified library slugs or improved result ranking.

## License

MIT
