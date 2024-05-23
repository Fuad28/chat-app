from django.db.models import TextChoices

class MessageTypeEnum(TextChoices):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"