# import pytest
# from databass import util
# from sqlalchemy.exc import DataError
# from datetime import datetime
#
#
# class TestImgExists:
#     # Tests for img_exists()
#     # TODO: move this into the tests for api/util.py Util class
#
#     @pytest.fixture
#     def mock_glob(self, mocker):
#         """Fixture to mock glob.glob"""
#         return mocker.patch('glob.glob')
#
#     @pytest.mark.parametrize(
#         'item_type,item_id',
#         [('release', 0), ('artist', -1), ('label', 1000000000000)]
#     )
#     def test_img_exists_not_found(self, item_type, item_id, mock_glob):
#         """
#         Test for an image that does not exist
#         """
#         mock_glob.return_value = False
#         result = util.img_exists(
#             item_type=item_type,
#             item_id=item_id
#         )
#         assert result is False
#
#     @pytest.mark.parametrize(
#         'item_type,item_id',
#         [('release', 2), ('ARTIST', 5), ('laBel', 10)]
#     )
#     def test_img_exists(self, item_type, item_id, mock_glob):
#         """
#         Test for an image that exists locally
#         """
#         mock_glob.return_value = [f"static/img/{item_type.lower()}/{item_id}.png"]
#
#         result = util.img_exists(
#             item_type=item_type,
#             item_id=item_id
#         )
#         assert result == f"/static/img/{item_type.lower()}/{item_id}.png"
#
#     @pytest.mark.parametrize(
#         'item_type,item_id',
#         [('release', 2.5), ('label', [1, 2]), ('artist', '1')]
#     )
#     def test_img_exists_invalid_item_id_type(self, item_type, item_id):
#         """
#         Test for correct handling of invalid item_id type
#         """
#         with pytest.raises(TypeError, match="item_id must be an integer."):
#             util.img_exists(item_type=item_type, item_id=item_id)
#
#     @pytest.mark.parametrize(
#         'item_type,item_id',
#         [(123, 2), ([1, 2], 5), (1.5, 5)]
#     )
#     def test_img_exists_invalid_item_type_type(self, item_type, item_id):
#         """
#         Test for correct handling of invalid item_type type
#         """
#         with pytest.raises(TypeError, match="item_type must be a string."):
#             util.img_exists(item_type=item_type, item_id=item_id)
#
#     @pytest.mark.parametrize(
#         'item_type,item_id',
#         [(' ', 2), ('asdf', 3)]
#     )
#     def test_img_exists_invalid_item_type(self, item_type, item_id):
#         """
#         Test for correct handling for when item_type is not equal to one of: release, artist, label
#         """
#         with pytest.raises(ValueError, match=f"Invalid item_type: {item_type}. "
#                                              f"Must be one of the following strings: {', '.join(["release", "artist",
#                                                                                                  "label"])}"
#                            ):
#             util.img_exists(item_id=item_id, item_type=item_type)
#
#     @pytest.mark.parametrize(
#         'item_type,item_id,file_extension',
#         [('release', 2, 'png'), ('ARTIST', 5, 'jpg'), ('laBel', 10, 'jpeg'), ('release', 100, 'gif')]
#     )
#     def test_img_exists_image_file_extensions(self, item_type, item_id, file_extension, mock_glob):
#         """
#         Test that function works with various image extensions
#         """
#         mock_glob.return_value = [f"static/img/{item_type}/{item_id}.{file_extension}"]
#
#         result = util.img_exists(
#             item_type=item_type,
#             item_id=item_id
#         )
#         assert result == f"/static/img/{item_type}/{item_id}.{file_extension}"

