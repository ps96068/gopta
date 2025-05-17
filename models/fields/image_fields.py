from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple, Type, Union
from sqlalchemy import types
# from sqlalchemy_file import FileField, ImageField
# from sqlalchemy_file.file import File
# from sqlalchemy_file.processors import Processor, ThumbnailGenerator
# from sqlalchemy_file.validators import ImageValidator, Validator




# class MyFileField(FileField):
#     pass

# class PostImageField(ImageField):
#     """ Redefinit """

    # impl = types.

    #
    # def __init__(
    #     self,
    #     *args: Tuple[Any],
    #     upload_storage: Optional[str] = None,
    #     thumbnail_size: Optional[Tuple[int, int]] = None,
    #     image_validator: Optional[ImageValidator] = None,
    #     validators: Optional[List[Validator]] = None,
    #     processors: Optional[List[Processor]] = None,
    #     upload_type: Type[File] = File,
    #     multiple: Optional[bool] = False,
    #     extra: Optional[Dict[str, str]] = None,
    #     headers: Optional[Dict[str, str]] = None,
    #     **kwargs: Dict[str, Any],
    # ) -> None:
    #     """Parameters
    #     upload_storage: storage to use
    #     image_validator: ImageField use default image
    #     validator, Use this property to customize it.
    #     thumbnail_size: If set, a thumbnail will be generated
    #     from original image using [ThumbnailGenerator]
    #     [sqlalchemy_file.processors.ThumbnailGenerator]
    #     validators: List of additional validators to apply
    #     processors: List of validators to apply
    #     upload_type: File class to use, could be
    #     used to set custom File class
    #     multiple: Use this to save multiple files
    #     extra: Extra attributes (driver specific).
    #     """
    #     if validators is None:
    #         validators = []
    #     if image_validator is None:
    #         image_validator = ImageValidator()
    #     if thumbnail_size is not None:
    #         if processors is None:
    #             processors = []
    #         processors.append(ThumbnailGenerator(thumbnail_size))
    #     validators.append(image_validator)
    #     super().__init__(
    #         *args,
    #         upload_storage=upload_storage,
    #         validators=validators,
    #         processors=processors,
    #         upload_type=upload_type,
    #         multiple=multiple,
    #         extra=extra,
    #         headers=headers,
    #         **kwargs,
    #     )



