# coding=utf-8
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
import pytest
import six

from devtools_testutils import AzureTestCase

from azure.containerregistry import (
    ContainerRegistryClient,
    DeleteRepositoryResult,
)
from azure.core.exceptions import ResourceNotFoundError
from azure.core.paging import ItemPaged
from azure.core.pipeline.transport import RequestsTransport

from testcase import ContainerRegistryTestClass
from constants import TO_BE_DELETED, HELLO_WORLD
from preparer import acr_preparer


class TestContainerRegistryClient(ContainerRegistryTestClass):
    @acr_preparer()
    def test_list_repositories(self, containerregistry_endpoint):
        client = self.create_registry_client(containerregistry_endpoint)

        repositories = client.list_repositories()
        assert isinstance(repositories, ItemPaged)

        count = 0
        prev = None
        for repo in repositories:
            count += 1
            assert isinstance(repo, six.string_types)
            assert prev != repo
            prev = repo

        assert count > 0

    @acr_preparer()
    def test_list_repositories_by_page(self, containerregistry_endpoint):
        client = self.create_registry_client(containerregistry_endpoint)
        results_per_page = 2
        total_pages = 0

        repository_pages = client.list_repositories(results_per_page=results_per_page)

        prev = None
        for page in repository_pages.by_page():
            page_count = 0
            for repo in page:
                assert isinstance(repo, six.string_types)
                assert prev != repo
                prev = repo
                page_count += 1
            assert page_count <= results_per_page
            total_pages += 1

        assert total_pages > 1

    @acr_preparer()
    def test_delete_repository(self, containerregistry_endpoint, containerregistry_resource_group):
        self.import_image(HELLO_WORLD, [TO_BE_DELETED])
        client = self.create_registry_client(containerregistry_endpoint)

        result = client.delete_repository(TO_BE_DELETED)
        assert isinstance(result, DeleteRepositoryResult)
        assert result.deleted_manifests is not None
        assert result.deleted_tags is not None

        for repo in client.list_repositories():
            if repo == TO_BE_DELETED:
                raise ValueError("Repository not deleted")

    @acr_preparer()
    def test_delete_repository_does_not_exist(self, containerregistry_endpoint):
        client = self.create_registry_client(containerregistry_endpoint)

        with pytest.raises(ResourceNotFoundError):
            deleted_result = client.delete_repository("not_real_repo")

    @acr_preparer()
    def test_transport_closed_only_once(self, containerregistry_endpoint):
        transport = RequestsTransport()
        client = self.create_registry_client(containerregistry_endpoint, transport=transport)
        with client:
            for r in client.list_repositories():
                pass
            assert transport.session is not None

            with client.get_repository_client(HELLO_WORLD) as repo_client:
                assert transport.session is not None

            for r in client.list_repositories():
                pass
            assert transport.session is not None
