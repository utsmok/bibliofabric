"""Retraction helpers on Work, checked against a real updated-by payload."""

from stavrophora import Work

# updated-by of 10.1177/1758835919874651 as the live API returned it on
# 2026-11-28, plus one correction that must not count as a retraction.
RETRACTED = {
    "DOI": "10.1177/1758835919874651",
    "updated-by": [
        {
            "DOI": "10.1177/17588359211061903",
            "type": "retraction",
            "label": "Retraction",
            "source": "retraction-watch",
            "updated": {"date-parts": [[2021, 12, 15]]},
            "record-id": "34999",
        },
        {
            "DOI": "10.1177/17588359211061903",
            "type": "retraction",
            "label": "Retraction",
            "source": "publisher",
            "updated": {"date-parts": [[2021, 12, 15]]},
        },
        {"DOI": "10.1177/1", "type": "correction", "source": "publisher"},
    ],
}


def test_retractions_keep_both_sources_and_skip_other_updates():
    work = Work.model_validate(RETRACTED)
    assert work.is_retracted
    assert [entry.source for entry in work.retractions] == [
        "retraction-watch",
        "publisher",
    ]
    assert work.retractions[0].record_id == "34999"
    assert work.retractions[1].record_id is None


def test_work_without_updates_is_not_retracted():
    work = Work.model_validate({"DOI": "10.1038/nature12373"})
    assert not work.is_retracted
    assert work.retractions == []
