class ModelInstanceRetriever:
    @classmethod
    def get_object(cls, model, id):
        try:
            obj = model.objects.get(id=id)
        except model.DoesNotExist:
            return None
        return obj

    @classmethod
    def get_instance_by_field(self, model, field_name, field_value):
        try:
            if not hasattr(model, field_name):
                raise AttributeError(
                    f"'{model.__name__}' has no attribute '{field_name}'"
                )
            kwargs = {field_name: field_value}
            return model.objects.filter(**kwargs).first()
        except Exception as e:
            return None

    @classmethod
    def get_instance_by_fields(self, model, fields_dict):
        try:
            for field_name in fields_dict.keys():
                if not hasattr(model, field_name):
                    raise AttributeError(
                        f"'{model.__name__}' has no attribute '{field_name}'"
                    )
            return model.objects.filter(**fields_dict).first()
        except Exception as e:
            return None
