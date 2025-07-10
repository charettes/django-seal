from django.apps import AppConfig, apps


class SealAppConfig(AppConfig):
    name = __package__

    def ready(self):
        from .descriptors import make_contenttypes_sealable
        from .models import SealableModel, make_model_sealable

        try:
            apps.get_app_config("contenttypes")
        except LookupError:
            pass
        else:
            make_contenttypes_sealable()

        for model in apps.get_models():
            opts = model._meta
            if opts.proxy or not issubclass(model, SealableModel):
                continue
            make_model_sealable(model)
