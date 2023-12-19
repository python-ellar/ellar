import typing as t
import urllib.parse
from io import BytesIO

from ellar.core.files.storages.base import BaseStorage

try:
    import boto3
except ImportError:
    boto3 = None


class S3AWSFileStorage(BaseStorage):  # pragma: no cover
    def service_name(self) -> str:
        return "s3_bucket"

    def __init__(
        self,
        bucket: str,
        access_key: str,
        secret_key: str,
        region: str,
        max_age: int = 60 * 60 * 24 * 365,
        prefix: t.Optional[str] = None,
        endpoint_url: t.Optional[str] = None,
        acl: str = "private",
        enable_cache_control: bool = False,
        public_link_expiration: int = 3600,
    ) -> None:
        if not boto3:
            raise RuntimeError(
                "boto3 must be installed to use the 'S3AWSFileStorage' class. pip install boto3"
            )

        self.bucket = self.get_aws_bucket(
            bucket=bucket,
            secret_key=secret_key,
            access_key=access_key,
            region=region,
            endpoint_url=endpoint_url,
        )
        self._max_age = max_age
        self._prefix = prefix
        self._acl = acl
        self._enable_cache_control = enable_cache_control
        self._public_link_expiration = public_link_expiration

    def get_aws_bucket(
        self,
        bucket: str,
        access_key: str,
        secret_key: str,
        region: str,
        endpoint_url: t.Optional[str] = None,
    ) -> t.Any:
        session = boto3.session.Session()
        config = boto3.session.Config(
            s3={"addressing_style": "path"}, signature_version="s3v4"
        )

        s3 = session.resource(
            "s3",
            config=config,
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        return s3.Bucket(bucket)

    def get_s3_path(self, filename: str) -> str:
        if self._prefix:
            filename = "{0}/{1}".format(self._prefix, filename)
        self.validate_file_name(filename)
        return self.generate_filename(filename)

    def _upload_file(
        self, filename: str, data: str, content_type: t.Optional[str], rrs: bool = False
    ) -> t.Any:
        put_object_kwargs = {
            "Key": filename,
            "Body": data,
            "ACL": self._acl,
            "StorageClass": "REDUCED_REDUNDANCY" if rrs else "STANDARD",
            "ContentType": content_type or "",
        }
        if self._enable_cache_control:
            put_object_kwargs.update(CacheControl="max-age=" + str(self._max_age))

        return self.bucket.put_object(**put_object_kwargs)

    def put(self, filename: str, stream: t.IO) -> int:
        path = self.get_s3_path(filename)
        stream.seek(0)
        data = stream.read()

        content_type = getattr(stream, "content_type", None)
        rrs = getattr(stream, "reproducible", False)

        self._upload_file(path, data, content_type, rrs=rrs)

        return len(data)

    def delete(self, filename: str) -> None:
        path = self.get_s3_path(filename)
        self.bucket.Object(path).delete()

    def open(self, filename: str, mode: str = "rb") -> t.IO:
        path = self.get_s3_path(filename)
        obj = self.bucket.Object(path).get()

        return BytesIO(obj["Body"].read())

    def _strip_signing_parameters(self, url: str) -> str:
        split_url = urllib.parse.urlsplit(url)
        qs = urllib.parse.parse_qsl(split_url.query, keep_blank_values=True)
        blacklist = {
            "x-amz-algorithm",
            "x-amz-credential",
            "x-amz-date",
            "x-amz-expires",
            "x-amz-signedheaders",
            "x-amz-signature",
            "x-amz-security-token",
            "awsaccesskeyid",
            "expires",
            "signature",
        }
        filtered_qs = ((key, val) for key, val in qs if key.lower() not in blacklist)
        joined_qs = ("=".join(keyval) for keyval in filtered_qs)
        split_url = split_url._replace(query="&".join(joined_qs))
        return split_url.geturl()

    def locate(self, filename: str) -> str:
        path = self.get_s3_path(filename)
        params = {"Key": path, "Bucket": self.bucket.name}
        expires = self._public_link_expiration

        url = self.bucket.meta.client.generate_presigned_url(
            "get_object", Params=params, ExpiresIn=expires
        )

        if self._acl in ["public-read", "public-read-write"]:
            url = self._strip_signing_parameters(url)

        return url  # type:ignore[no-any-return]
