
from django.db import models


class LookupCountry(models.Model):
    country_code = models.CharField(max_length=30, blank=True, null=True)
    country_name = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return "<{}>".format(self.country_name)

    class Meta:
        managed = True
        db_table = 'lookup_country'
        verbose_name_plural = "Lookup countries"


class LookupState(models.Model):
    country = models.ForeignKey(LookupCountry, models.DO_NOTHING, blank=True, null=True)
    state_code = models.CharField(max_length=30, blank=True, null=True)
    state_name = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return "<{}>".format(self.state_name)

    class Meta:
        managed = True
        db_table = 'lookup_state'


class LookupDegreeType(models.Model):
    id = models.BigAutoField(primary_key=True)
    degree_type_name = models.CharField(max_length=50, blank=True, null=False)
    degree_type_sovren = models.CharField(max_length=50, blank=True, null=True)
    visible = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'lookup_degree_type'


class LookupDegreeName(models.Model):
    id = models.BigAutoField(primary_key=True)
    degree_type = models.ForeignKey(LookupDegreeType, models.DO_NOTHING, blank=True, null=True)
    degree_name = models.CharField(max_length=128, blank=True, null=False)
    degree_abbreviation = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'lookup_degree_name'


class LookupDegreeMajor(models.Model):
    id = models.BigAutoField(primary_key=True)
    degree_major_name = models.CharField(max_length=128, blank=True, null=False)

    class Meta:
        managed = True
        db_table = 'lookup_degree_major'


class LookupPhysicalLocation(models.Model):
    id = models.BigAutoField(primary_key=True)
    city = models.CharField(max_length=1000, db_index=True)
    state = models.ForeignKey(LookupState, null=True)
    latitude = models.FloatField(null=True, db_index=True)
    longitude = models.FloatField(null=True, db_index=True)

    class Meta:
        db_table = "lookup_physical_location"


class LookupCandidateStatus(models.Model):
    status = models.CharField(max_length=256, blank=False, null=False)
    order = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "lookup_candidate_status"


class LookupRegion(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.TextField(blank=False, null=False, db_index=True)
    city = models.CharField(max_length=1000, null=False, blank=False)
    state = models.ForeignKey(LookupState)

    radius = models.FloatField(null=True)  # in miles

    class Meta:
        db_table = "lookup_region"


class LookupDeclineReason(models.Model):
    id = models.BigAutoField(primary_key=True)
    reason = models.CharField(max_length=256, null=False, blank=False)
    order = models.IntegerField(null=False, blank=False)

    class Meta:
        db_table = "lookup_decline_reason"


class LookupRejectReason(models.Model):
    id = models.BigAutoField(primary_key=True)
    reason = models.CharField(max_length=256, null=False, blank=False)
    order = models.IntegerField(null=False, blank=False)

    class Meta:
        db_table = "lookup_reject_reason"


class LookupIndustry(models.Model):
    id = models.BigAutoField(primary_key=True)
    industry_name = models.CharField(max_length=256)

    class Meta:
        db_table = "lookup_industry"


class LookupZipCode(models.Model):
    id = models.BigAutoField(primary_key=True)
    zip_code = models.CharField(max_length=10, unique=True, db_index=True)
    city = models.CharField(max_length=128, db_index=True)
    state = models.ForeignKey(LookupState)
    latitude = models.FloatField(null=True, db_index=True)
    longitude = models.FloatField(null=True, db_index=True)

    class Meta:
        db_table = "lookup_zip_code"
