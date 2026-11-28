"""The public journal CSV export: redirect-following download and row reader."""

from diurnalia import DOAJ_JOURNAL_CSV_URL, iter_journal_csv

S3_URL = "https://doaj-live-journal-csv.s3.amazonaws.com/doaj_journalcsv.csv"

CSV_BODY = (
    "\ufeffJournal title,Journal ISSN (print version),Journal EISSN (online version)\r\n"
    'PLOS ONE,,1932-6203\r\n"Journal, with comma",1234-5678,\r\n'
).encode()


async def test_download_csv_follows_the_redirect_and_reads_rows(
    client, httpx_mock, tmp_path
):
    httpx_mock.add_response(
        url=DOAJ_JOURNAL_CSV_URL, status_code=307, headers={"Location": S3_URL}
    )
    httpx_mock.add_response(url=S3_URL, content=CSV_BODY)
    path = await client.journals.download_csv(tmp_path / "nested" / "journals.csv")
    assert path.read_bytes() == CSV_BODY
    rows = list(iter_journal_csv(path))
    assert rows == [
        {
            "Journal title": "PLOS ONE",
            "Journal ISSN (print version)": "",
            "Journal EISSN (online version)": "1932-6203",
        },
        {
            "Journal title": "Journal, with comma",
            "Journal ISSN (print version)": "1234-5678",
            "Journal EISSN (online version)": "",
        },
    ]
