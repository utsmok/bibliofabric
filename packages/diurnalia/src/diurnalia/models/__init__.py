"""Pydantic models for DOAJ journals and articles."""

from .article import Article, ArticleBibjson, ArticleJournal, Author, Identifier, Link
from .common import Admin, Subject
from .journal import (
    Apc,
    ArticleDisplay,
    Copyright,
    DepositPolicy,
    Editorial,
    Journal,
    JournalBibjson,
    JournalPublisher,
    License,
    OtherCharges,
    PidScheme,
    Plagiarism,
    Preservation,
    Price,
    Ref,
    Waiver,
)

__all__ = [
    "Admin",
    "Apc",
    "Article",
    "ArticleBibjson",
    "ArticleDisplay",
    "ArticleJournal",
    "Author",
    "Copyright",
    "DepositPolicy",
    "Editorial",
    "Identifier",
    "Journal",
    "JournalBibjson",
    "JournalPublisher",
    "License",
    "Link",
    "OtherCharges",
    "PidScheme",
    "Plagiarism",
    "Preservation",
    "Price",
    "Ref",
    "Subject",
    "Waiver",
]
