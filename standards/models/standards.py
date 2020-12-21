
from django.conf import settings
from django.db.models import CASCADE
from django.db.models import CharField
from django.db.models import DateField
from django.db.models import DateTimeField
from django.db.models import FloatField
from django.db.models import ForeignKey
from django.db.models import JSONField
from django.db.models import ManyToManyField
from django.db.models import Model
from django.db.models import SET_NULL
from django.db.models import TextField
from django.db.models import URLField
from django.db.models import Q, UniqueConstraint
from model_utils import Choices
from mptt.models import MPTTModel
from mptt.models import TreeForeignKey
from standards.fields import ShortUUIDField


from .jurisdictions import Jurisdiction
from .terms import Term




# CURRICULUM STANDARDS
################################################################################

DIGITIZATION_METHODS = Choices(
    ("manual_entry",    "Manual data entry"),
    ("manual_scan",     "Manual data entry based on OCR"),
    ("automated_scan",  "Semi-automated stucture extraction through OCR"),
    ("website_scrape",  "Curriculum data scraped from website"),
    ("hackathon_import", "Curriculum data imported from Hackathon DB"),
    ("asn_import",      "Curriculum data imported from Achievement Standards Network (ASN)"),
    ("case_import",     "Curriculum data imported from CASE registry"),
)

PUBLICATION_STATUSES = Choices(
    ("draft",       "Draft"),
    ("published",   "Published (active)"),
    ("retired",     "Retired, deprecated, or superceded"),
)

class StandardsDocument(Model):
    """
    General Stores the metadata for a curriculum standard, usually one document.
    """
    # IDs
    id = ShortUUIDField(primary_key=True, editable=False, prefix='D')
    name = CharField(unique=True, max_length=200, help_text="A short, unique name for the document, e.g. CCSSM")
    # uri = computed field = localhost + get_absolute_url()
    #
    # Document info
    jurisdiction = ForeignKey(Jurisdiction, related_name="documents", on_delete=CASCADE, help_text='Jurisdiction of standards document')
    title = CharField(max_length=200, help_text="The offficial title of the document")
    description = TextField(blank=True, null=True, help_text="Detailed info about this document")
    language = CharField(max_length=20, blank=True, null=True, help_text="BCP47/RFC5646 codes like en, es, fr-CA.")
    publisher = CharField(max_length=200, blank=True, null=True, help_text="The name of the organizaiton publishing the document")
    version = CharField(max_length=50, blank=True, null=True, help_text="Document version or edition")
    #
    # Licensing
    license	= ForeignKey(Term, related_name='+', blank=True, null=True, on_delete=SET_NULL, limit_choices_to={'vocabulary__kind': 'license_kinds'})
    license_description	= TextField(blank=True, null=True, help_text="Full text of the document's licencing information")
    copyright_holder = CharField(max_length=200, blank=True, null=True, help_text="Name of organization that holds the copyright to the document")
    #
    # Educational domain
    subjects = ManyToManyField(Term, blank=True, related_name="+", limit_choices_to={'vocabulary__kind': 'subjects'})
    education_levels = ManyToManyField(Term, blank=True, related_name="+", limit_choices_to={'vocabulary__kind': 'education_levels'})
    date_valid = DateField(blank=True, null=True, help_text="Date when document started being valid")
    date_retired = DateField(blank=True, null=True, help_text="Date when document stopped being valid")
    #
    # Digitization domain
    digitization_method = CharField(max_length=200, choices=DIGITIZATION_METHODS, help_text="Digitization method")
    source_doc = URLField(max_length=512, blank=True, help_text="Where the data of this document was imported from")
    publication_status	= CharField(max_length=30, choices=PUBLICATION_STATUSES, default=PUBLICATION_STATUSES.draft)
    #
    # Publishing domain
    canonical_uri = URLField(max_length=512, null=True, blank=True, help_text="URI for the document used when publishing")
    source_uri = URLField(max_length=512, null=True, blank=True, help_text="External URI for imported document")
    source_id = CharField(max_length=100, blank=True, help_text="An external identifier (usually part of source_uri)")
    #
    # Metadata
    notes = TextField(blank=True, null=True, help_text="Additional notes about the document")
    date_created = DateTimeField(auto_now_add=True, help_text="When the standards document was added to repository.")
    date_modified = DateTimeField(auto_now=True, help_text="Date of last modification to document metadata.")
    extra_fields = JSONField(default=dict, blank=True)  # for data extensibility

    def __str__(self):
        return "{} ({})".format(self.title, self.id)

    def get_absolute_url(self):
        return "/documents/" + self.id

    @property
    def uri(self):
        return self.get_absolute_url()

    @property
    def root(self):
        return StandardNode.get_root_nodes().get(document=self)



class StandardNode(MPTTModel):
    """
    An individual standard noe within the a curriculum standards document.
    """
    # IDs
    id = ShortUUIDField(primary_key=True, editable=False, prefix='S')
    #
    # Structural
    parent = TreeForeignKey('self', on_delete=CASCADE, null=True, blank=True, related_name='children')
    document = ForeignKey(StandardsDocument, related_name="nodes", on_delete=CASCADE)
    kind = ForeignKey(Term, related_name='+', blank=True, null=True, on_delete=SET_NULL, limit_choices_to={'vocabulary__kind': 'curriculum_elements'})
    sort_order = FloatField(default=1.0)   # the position of node within parent
    #
    # Node attributes
    notation = CharField(max_length=200, blank=True, help_text="A human-referenceable code for this node")
    # alt_notations: TODO impl as ArrayField after move to Postgres DB
    list_id = CharField(max_length=50, blank=True, help_text="A character or symbol denoting the node position with a list")
    title = CharField(max_length=200, blank=True, help_text="An optional heading or abbreviated description")
    description	= TextField(help_text="Primary text that describes this node")
    language = CharField(max_length=20, blank=True, null=True, help_text="BCP47/RFC5646 codes like en, es, fr-CA.")
    #
    # Educational domain
    subjects = ManyToManyField(Term, blank=True, related_name="+", limit_choices_to={'vocabulary__kind': 'subjects'})
    education_levels = ManyToManyField(Term, blank=True, related_name="+", limit_choices_to={'vocabulary__kind': 'education_levels'})
    concept_terms = ManyToManyField(Term, blank=True, related_name="+", limit_choices_to={'vocabulary__kind': 'contept_terms'})
    concept_keywords = CharField(max_length=500, blank=True, null=True, help_text="Free form, comma-separated keywords")
    # MAYBE ADD
    # cognitive_process_dimensions	m2m --> Term.vocabulary[kind=cognitive_process_dimensions]
    # knowledge_dimensions		    m2m --> Term[kind=knowledge_dimensions]
    #
    # Publishing domain
    path = CharField(max_length=200, blank=True, help_text="Full path of node. Usually ends in notation.")
    canonical_uri = URLField(max_length=512, null=True, blank=True, help_text="URI for the standard node used when publishing")
    source_uri = URLField(max_length=512, null=True, blank=True, help_text="External URI for imported standard nodes")
    source_id = CharField(max_length=100, blank=True, help_text="An external identifier (usually part of source_uri)")
    #
    # Metadata
    notes = TextField(blank=True, null=True, help_text="Additional notes and supporting text")
    date_created = DateTimeField(auto_now_add=True, help_text="When the node was added to repository")
    date_modified = DateTimeField(auto_now=True, help_text="Date of last modification to node")
    extra_fields = JSONField(default=dict, blank=True)  # for data extensibility


    class Meta:
        # Make sure every document has at most one tree
        constraints = [
            UniqueConstraint(
                name="single_root_per_document",
                fields=["document", "tree_id"],
                condition=Q(level=0),
            )
        ]
        ordering = ('sort_order', )

    class MPTTMeta:
        order_insertion_by = ['sort_order']

    def __str__(self):
        description_start = self.description[0:30] + '...'
        return "{} ({})".format(description_start, self.id)

    def get_absolute_url(self):
        return "/standardnodes/" + self.id

    @property
    def uri(self):
        return self.get_absolute_url()

    def add_child(self, **kwargs):
        if "document" not in kwargs:
            kwargs["document"] = self.document
        return super().add_child(**kwargs)




# # CROSSWALKS
# ################################################################################

# class StandardsCrosswalk(Model):
#     id = ShortUUIDField(primary_key=True, default=uuid.uuid4, editable=False)


# class StandardNodeRelation(Model):
#     id = ShortUUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     crosswalk = ForeignKey(StandardsCrosswalk, related_name="edges", on_delete=CASCADE)
