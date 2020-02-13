
__author__ = "tplick"

from django.db import models


# Table: bg_alternate_titles
#
# Columns:
# id: int(11) AI PK
# onet_id: varchar(50)
# alt_title: text
# active_status: int(11)

class BgAlternateTitles(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_id = models.CharField(max_length=50, db_index=True)
    alt_title = models.TextField(db_index=True)
    active_status = models.IntegerField()

    class Meta:
        db_table = "bg_alternate_titles"


# Table: bg_position_master
#
# Columns:
# id: int(11) AI PK
# onet_soc_code: varchar(50)
# title: text
# description: text
# job_family: varchar(255)
# industry_id: int(10)
# active_status: int(11)

class BgPositionMaster(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_soc_code = models.CharField(max_length=50, db_index=True)
    title = models.TextField(db_index=True)
    description = models.TextField()
    job_family = models.CharField(max_length=255)
    industry_id = models.IntegerField(db_index=True)
    active_status = models.IntegerField()

    class Meta:
        db_table = "bg_position_master"


# Table: bg_onet_abilities
#
# Columns:
# id int(11) AI PK
# onet_id varchar(45)
# element_id varchar(45)
# element_name varchar(150)
# scale_id varchar(20)
# scale_name varchar(45)
# data_value float
# active_status int(10)

class BgOnetAbilities(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_id = models.CharField(max_length=45, db_index=True)
    element_id = models.CharField(max_length=45, db_index=True)
    element_name = models.CharField(max_length=150)
    scale_id = models.CharField(max_length=20, db_index=True)
    scale_name = models.CharField(max_length=45)
    data_value = models.FloatField()
    active_status = models.IntegerField()

    class Meta:
        db_table = "bg_onet_abilities"


# Table: bg_onet_career_changers_matrix
#
# Columns:
# id int(11) AI PK
# onet_id varchar(45)
# related_onet_id varchar(45)
# index int(10)
# active_status int(10)

class BgOnetCareerChangersMatrix(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_id = models.CharField(max_length=45, db_index=True)
    related_onet_id = models.CharField(max_length=45, db_index=True)
    index = models.IntegerField()
    active_status = models.IntegerField()

    class Meta:
        db_table = "bg_onet_career_changers_matrix"


# Table: bg_onet_category
#
# Columns:
# id int(11) AI PK
# scale_id varchar(20)
# scale_name varchar(45)
# category int(5)
# category_description varchar(100)

class BgOnetCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    scale_id = models.CharField(max_length=20, db_index=True)
    scale_name = models.CharField(max_length=45)
    category = models.IntegerField(db_index=True)
    category_description = models.CharField(max_length=100)

    class Meta:
        db_table = "bg_onet_category"


# Table: bg_onet_knowledge
#
# Columns:
# id int(11) AI PK
# onet_id varchar(45)
# element_id varchar(45)
# element_name varchar(150)
# scale_id varchar(20)
# scale_name varchar(45)
# data_value float
# active_status int(10)

class BgOnetKnowledge(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_id = models.CharField(max_length=45, db_index=True)
    element_id = models.CharField(max_length=45, db_index=True)
    element_name = models.CharField(max_length=150)
    scale_id = models.CharField(max_length=20, db_index=True)
    scale_name = models.CharField(max_length=45)
    data_value = models.FloatField()
    active_status = models.IntegerField()

    class Meta:
        db_table = "bg_onet_knowledge"


# Table: bg_onet_skills
#
# Columns:
# id int(11) AI PK
# onet_id varchar(45)
# element_id varchar(45)
# element_name varchar(150)
# scale_id varchar(20)
# scale_name varchar(45)
# data_value float
# active_status int(10)

class BgOnetSkills(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_id = models.CharField(max_length=45, db_index=True)
    element_id = models.CharField(max_length=45, db_index=True)
    element_name = models.CharField(max_length=150)
    scale_id = models.CharField(max_length=20, db_index=True)
    scale_name = models.CharField(max_length=45)
    data_value = models.FloatField()
    active_status = models.IntegerField()

    class Meta:
        db_table = "bg_onet_skills"


# Table: bg_onet_task_ratings
#
# Columns:
# id int(11) AI PK
# onet_id varchar(45)
# task_id varchar(45)
# task text
# scale_id varchar(20)
# scale_name varchar(100)
# category int(5)
# data_value float
# active_status int(10)

class BgOnetTaskRatings(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_id = models.CharField(max_length=45, db_index=True)
    task_id = models.CharField(max_length=45, db_index=True)
    task = models.TextField()
    scale_id = models.CharField(max_length=20, db_index=True)
    scale_name = models.CharField(max_length=100)
    category = models.IntegerField(db_index=True)
    data_value = models.FloatField()
    active_status = models.IntegerField()

    class Meta:
        db_table = "bg_onet_task_ratings"


# Table: bg_onet_task_to_dwas
#
# Columns:
# id int(11) AI PK
# onet_id varchar(45)
# task_id varchar(45)
# task text
# dwa_id varchar(50)
# dwa_title varchar(255)
# data_value float
# active_status int(10)

class BgOnetTaskToDwas(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_id = models.CharField(max_length=45, db_index=True)
    task_id = models.CharField(max_length=45, db_index=True)
    task = models.TextField()
    dwa_id = models.CharField(max_length=50, db_index=True)
    dwa_title = models.CharField(max_length=255)
    data_value = models.FloatField()
    active_status = models.IntegerField()

    class Meta:
        db_table = "bg_onet_task_to_dwas"


# Table: bg_onet_tools_tech
#
# Columns:
# id int(11) AI PK
# onet_id varchar(45)
# t2_type varchar(255)
# t2_example text


class BgOnetToolsTech(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_id = models.CharField(max_length=45, db_index=True)
    t2_type = models.CharField(max_length=255)
    t2_example = models.TextField()

    class Meta:
        db_table = "bg_onet_tools_tech"


# Table: bg_onet_work_activities
#
# Columns:
# id int(11) AI PK
# onet_id varchar(45)
# element_id varchar(45)
# element_name varchar(150)
# scale_id varchar(20)
# scale_name varchar(45)
# data_value float
# active_status int(10)

class BgOnetWorkActivities(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_id = models.CharField(max_length=45, db_index=True)
    element_id = models.CharField(max_length=45, db_index=True)
    element_name = models.CharField(max_length=150)
    scale_id = models.CharField(max_length=20, db_index=True)
    scale_name = models.CharField(max_length=45)
    data_value = models.FloatField()
    active_status = models.IntegerField()

    class Meta:
        db_table = "bg_onet_work_activities"


# Table: bg_onet_work_context
#
# Columns:
# id int(11) AI PK
# onet_id varchar(45)
# element_id varchar(45)
# element_name varchar(150)
# scale_id varchar(20)
# scale_name varchar(45)
# data_value float
# active_status int(10)

class BgOnetWorkContext(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_id = models.CharField(max_length=45, db_index=True)
    element_id = models.CharField(max_length=45, db_index=True)
    element_name = models.CharField(max_length=150)
    scale_id = models.CharField(max_length=20, db_index=True)
    scale_name = models.CharField(max_length=45)
    data_value = models.FloatField()
    active_status = models.IntegerField()

    class Meta:
        db_table = "bg_onet_work_context"


# Table: bg_onet_work_styles
#
# Columns:
# id int(11) AI PK
# onet_id varchar(45)
# element_id varchar(45)
# element_name varchar(150)
# scale_id varchar(20)
# scale_name varchar(45)
# data_value float
# active_status int(10)

class BgOnetWorkStyles(models.Model):
    id = models.BigAutoField(primary_key=True)
    onet_id = models.CharField(max_length=45, db_index=True)
    element_id = models.CharField(max_length=45, db_index=True)
    element_name = models.CharField(max_length=150)
    scale_id = models.CharField(max_length=20, db_index=True)
    scale_name = models.CharField(max_length=45)
    data_value = models.FloatField()
    active_status = models.IntegerField()

    class Meta:
        db_table = "bg_onet_work_styles"
