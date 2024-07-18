from django.db.models import Transform
from django.db.models.lookups import GaussDBOperatorLookup
from django.db.models.sql.query import Query

from .search import SearchVector, SearchVectorExact, SearchVectorField


class DataContains(GaussDBOperatorLookup):
    lookup_name = "contains"
    gaussdb_operator = "@>"


class ContainedBy(GaussDBOperatorLookup):
    lookup_name = "contained_by"
    gaussdb_operator = "<@"


class Overlap(GaussDBOperatorLookup):
    lookup_name = "overlap"
    gaussdb_operator = "&&"

    def get_prep_lookup(self):
        from .expressions import ArraySubquery

        if isinstance(self.rhs, Query):
            self.rhs = ArraySubquery(self.rhs)
        return super().get_prep_lookup()


class HasKey(GaussDBOperatorLookup):
    lookup_name = "has_key"
    gaussdb_operator = "?"
    prepare_rhs = False


class HasKeys(GaussDBOperatorLookup):
    lookup_name = "has_keys"
    gaussdb_operator = "?&"

    def get_prep_lookup(self):
        return [str(item) for item in self.rhs]


class HasAnyKeys(HasKeys):
    lookup_name = "has_any_keys"
    gaussdb_operator = "?|"


class Unaccent(Transform):
    bilateral = True
    lookup_name = "unaccent"
    function = "UNACCENT"


class SearchLookup(SearchVectorExact):
    lookup_name = "search"

    def process_lhs(self, qn, connection):
        if not isinstance(self.lhs.output_field, SearchVectorField):
            config = getattr(self.rhs, "config", None)
            self.lhs = SearchVector(self.lhs, config=config)
        lhs, lhs_params = super().process_lhs(qn, connection)
        return lhs, lhs_params


class TrigramSimilar(GaussDBOperatorLookup):
    lookup_name = "trigram_similar"
    gaussdb_operator = "%%"


class TrigramWordSimilar(GaussDBOperatorLookup):
    lookup_name = "trigram_word_similar"
    gaussdb_operator = "%%>"


class TrigramStrictWordSimilar(GaussDBOperatorLookup):
    lookup_name = "trigram_strict_word_similar"
    gaussdb_operator = "%%>>"
