from django.db import models
from django.utils import timezone


class EmailLog(models.Model):
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50)
    error_message = models.TextField(null=True, blank=True)
    smtp_server = models.CharField(max_length=255, null=True, blank=True)
    provider = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.subject} to {self.recipient}"


class SystemConfig(models.Model):
    # CONFIG_CHOICES = [
    #     ('PAYMENT_GATEWAY', 'Payment Gateway'),
    #     ('EMAIL_PROVIDER', 'Email Provider'),
    #     # Add other configurations as needed
    # ]
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=255)
    valid_choices = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configurations"

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_value(cls, key):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return None

    @classmethod
    def set_config_value(cls, key, value):
        """Set or update the value for a given configuration key."""
        config, created = cls.objects.get_or_create(key=key)
        config.set_value(value)

    def is_valid_value(self, value):
        """Check if the given value is valid for this key based on valid_choices."""
        return value in self.valid_choices

    def set_value(self, value):
        """Set the value for this configuration and save it."""
        self.value = value
        self.save()

    def get_valid_choices(self):
        """Return the valid choices for this configuration key."""
        return self.valid_choices

    def set_valid_choices(self, new_choices):
        """Add new choices to the valid choices array and save it."""
        current_choices = set(self.valid_choices)
        updated_choices = current_choices.union(new_choices)
        self.valid_choices = list(updated_choices)
        self.save()
