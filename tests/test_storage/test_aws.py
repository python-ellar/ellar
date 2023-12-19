import pytest
from ellar.core.files.storages.aws_s3 import S3AWSFileStorage


def test_aws_storage_boto3_package_unavailable():
    with pytest.raises(RuntimeError):
        S3AWSFileStorage(
            bucket="ellar", access_key="none", secret_key="none", region="not necessary"
        )
