# Copyright 2024 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import platform
import shutil
from abc import abstractmethod
from io import BufferedIOBase
from pathlib import Path
from typing import Dict

import s3fs
from botocore import exceptions as s3_exceptions

from secretflow.spec.v1.data_pb2 import StorageConfig


class StorageImplBase:
    def __init__(self) -> None:
        pass

    @abstractmethod
    def download_file(self, remote_fn, local_fn) -> None:
        """blocked download whole file into local_fn, overwrite if local_fn exist"""
        pass

    @abstractmethod
    def upload_file(self, remote_fn, local_fn) -> None:
        """blocked upload_file whole file into remote_fn, overwrite if remote_fn exist"""
        pass

    @abstractmethod
    def get_reader(self, remote_fn) -> BufferedIOBase:
        pass

    @abstractmethod
    def get_writer(self, remote_fn) -> BufferedIOBase:
        pass

    @abstractmethod
    def get_file_meta(self, remote_fn) -> Dict:
        pass


class S3StorageImpl(StorageImplBase):
    def __init__(self, config: StorageConfig) -> None:
        super().__init__()
        assert config.type == "s3"
        config: StorageConfig.S3Config = config.s3
        self._prefix = config.prefix
        self._bucket = config.bucket

        if config.version == "":
            config.version = "s3v4"

        assert config.version in [
            "s3v4",
            "s3v2",
        ], f"Not support version {config.version}"
        assert config.endpoint.startswith("https://") or config.endpoint.startswith(
            "http://"
        ), f"Please specify the scheme(http or https) of endpoint"
        self._s3_client = s3fs.S3FileSystem(
            anon=False,
            key=config.access_key_id,
            secret=config.access_key_secret,
            client_kwargs={'endpoint_url': config.endpoint},
            config_kwargs={
                'signature_version': config.version,
                's3': {
                    "addressing_style": "virtual" if config.virtual_host else "path"
                },
            },
        )

        try:
            self._s3_client.ls(self._bucket, detail=False)
        except s3_exceptions.UnknownSignatureVersionError as e:
            logging.exception(f"config.version {config.version} not support by server")
            raise
        except Exception as e:
            self._log_s3_error(e)
            raise

    def _log_s3_error(self, e: Exception, file_name: str = None) -> None:
        if isinstance(e, FileNotFoundError):
            if file_name:
                logging.exception(
                    f"The file {file_name} in bucket {self._bucket} does not exist"
                )
            else:
                logging.exception(f"The specified bucket {self._bucket} does not exist")
        elif isinstance(e, PermissionError):
            logging.exception("Access denied, Check your key and signing method")
        else:
            logging.exception("Unknown error")

    def _full_remote_fn(self, remote_fn):
        return f"s3://{os.path.join(self._bucket, self._prefix, remote_fn)}"

    def download_file(self, remote_fn, local_fn) -> None:
        """blocked download whole file into local_fn, overwrite if local_fn exist"""
        full_remote_fn = self._full_remote_fn(remote_fn)
        try:
            self._s3_client.download(full_remote_fn, local_fn)
        except Exception as e:
            self._log_s3_error(e)
            raise

    def upload_file(self, remote_fn, local_fn) -> None:
        """blocked upload whole file into remote_fn, overwrite if remote_fn exist"""
        full_remote_fn = self._full_remote_fn(remote_fn)
        try:
            self._s3_client.upload(local_fn, full_remote_fn)
        except Exception as e:
            self._log_s3_error(e)
            raise

    def get_reader(self, remote_fn) -> BufferedIOBase:
        full_remote_fn = self._full_remote_fn(remote_fn)
        try:
            return self._s3_client.open(full_remote_fn, "rb")
        except Exception as e:
            self._log_s3_error(e)
            raise

    def get_writer(self, remote_fn) -> BufferedIOBase:
        full_remote_fn = self._full_remote_fn(remote_fn)
        try:
            return self._s3_client.open(full_remote_fn, "wb")
        except Exception as e:
            self._log_s3_error(e)
            raise

    def get_file_meta(self, remote_fn) -> Dict:
        full_remote_fn = self._full_remote_fn(remote_fn)
        try:
            meta = self._s3_client.stat(full_remote_fn)
            ret = {
                "LastModified": meta["LastModified"],
                "size": meta["size"],
                "ETag": meta["ETag"],
            }
            return ret
        except Exception as e:
            self._log_s3_error(e)
            raise


class LocalStorageImpl(StorageImplBase):
    def __init__(self, config: StorageConfig) -> None:
        super().__init__()
        assert config.type == "local_fs"
        self._local_wd = config.local_fs.wd

    def download_file(self, remote_fn, local_fn) -> None:
        """blocked download whole file into local_fn, overwrite if local_fn exist"""
        full_remote_fn = os.path.join(self._local_wd, remote_fn)
        assert os.path.exists(full_remote_fn)
        assert os.path.isfile(full_remote_fn)
        if os.path.exists(local_fn):
            assert os.path.isfile(local_fn)
            if os.path.samefile(full_remote_fn, local_fn):
                return
        Path(local_fn).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(full_remote_fn, local_fn)

    def upload_file(self, remote_fn, local_fn) -> None:
        """blocked upload_file whole file into remote_fn, overwrite if remote_fn exist"""
        assert os.path.exists(local_fn)
        assert os.path.isfile(local_fn)
        full_remote_fn = os.path.join(self._local_wd, remote_fn)

        assert not os.path.exists(full_remote_fn) or os.path.isfile(full_remote_fn)
        if os.path.exists(full_remote_fn):
            assert os.path.isfile(full_remote_fn)
            if os.path.samefile(full_remote_fn, local_fn):
                return
        Path(full_remote_fn).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local_fn, full_remote_fn)

    def get_reader(self, remote_fn) -> BufferedIOBase:
        full_remote_fn = os.path.join(self._local_wd, remote_fn)
        assert os.path.exists(full_remote_fn)
        assert os.path.isfile(full_remote_fn)
        return open(full_remote_fn, "rb")

    def get_writer(self, remote_fn) -> BufferedIOBase:
        full_remote_fn = os.path.join(self._local_wd, remote_fn)
        Path(full_remote_fn).parent.mkdir(parents=True, exist_ok=True)
        assert not os.path.exists(full_remote_fn) or os.path.isfile(full_remote_fn)
        return open(full_remote_fn, "wb")

    def get_file_meta(self, remote_fn) -> Dict:
        full_remote_fn = os.path.join(self._local_wd, remote_fn)
        assert os.path.exists(full_remote_fn)
        ret = {
            "ctime": os.path.getctime(full_remote_fn),
            "mtime": os.path.getmtime(full_remote_fn),
            "size": os.path.getsize(full_remote_fn),
        }
        if platform.system() == 'Linux':
            ret["inode"] = os.stat(full_remote_fn).st_ino
        return ret


def BuildStorageImpl(config: StorageConfig) -> StorageImplBase:
    if config.type.lower() == "s3":
        return S3StorageImpl(config)
    elif config.type.lower() == "local_fs":
        return LocalStorageImpl(config)
    else:
        # TODO: kuscia data proxy impl
        raise AttributeError(f"unsupported StorageConfig type {config.type}")
