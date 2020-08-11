# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

## [0.3.0] - 2020-08-11

### Added

- New management command `eveuniverse_load_types` making it easier for apps to preload the eve objects they need
- New manager method `bulk_get_or_create_esi()` for bulk loading of new eve objects.
- Type hints for all methods
- Improved documentation

### Changed

- Renamed methods that are supposed to be only used internally:
  - models.EveUniverseBaseModel: esi_mapping()
  - models.EveUniverseEntityModel and inherited models: inline_objects(), children(), esi_pk(), has_esi_path_list(), esi_path_list(), esi_path_object(), is_list_only_endpoint()
- Renamed entity_id parameter in helpers.EveEntityNameResolver.to_name()

### Fixed

## [0.2.0] - 2020-07-27

### Added

- Initial public release
