# JSON API Mock Server

## Purpose

Set up a mock server that accomplishes the following:

1. Unblocks front end
2. Has testing to ensure that mock response structures don't drift from master definitions

## Using mock server

### Endpoints and actions

##### `GET /resources/<id>`

* Returns a 200 JsonAPI response with the attributes defined in the corresponding Resource class, and all `id`s replaced with the requested resource id.

##### `PATCH /resources/<id>`

* Returns a 200 JsonAPI response with the attributes defined in the corresponding Resource class.
* If the patched data contain new attributes, those new attributes will be reflected in the returned response. Patched data containing relationships are still a TODO.

##### `DELETE /resources/<id>`

* Returns a 204 response.

##### `GET /resources`

* Returns a 200 JsonAPI response with a list of resource objects.
* Each resource object is created using definitions in the Resource class, but assigns each resource an incremental resource id.

##### `POST /resources`

* Returns a 201 JsonAPI response created using the attributes passed in as POST data.
* Note: Does not do any actual validation of the POST data.


### Json API query parameters

Mock server supports the following query parameters as defined in the JsonAPI spec.

Query parameter | Valid for | Details
--------------- | --------- | -----------
`?filter=<int>` | `GET /resources` | [see below](#filter)
`?include=<string>` | `GET /resources` and `GET /resource/<id>` | [see below](#include)
`?page_size=<int>` | `GET /resources` | [see below](#page_size)
`?page=<int>` | `GET /resources` | [see below](#page)

#### filter
Mock server does not actually apply filter criteria, but instead mimics it by returning half the list of resource objects. If both `?length=x` and `?filter=y` are provided, filter will return `x/2` objects.

#### include
Mock server returns an `included` object in the top level of the returned JsonAPI document. This object includes resource type and intermediary related resource types specified by the query parameter, and supports multiple, comma-separated parameters. For example, the `GET /resource?include=x.y,z` response contains an `included` object list with resource types `x`, `y` and `z`.

#### page_size
Mock server applies a page size of `x` to its returned results.

#### page
Mock server returns page `x` of its generated results.


### Hooks

Mock server exposes a number of "hooks" that allow consumers to specify certain scenarios or data for mock server to emulate. These hooks are:

1. HTTP __status code__
2. Resource __attributes__
3. Resource list __length__
4. POST __errors__
5. Disable __fake data__

By default, mock server recognizes two different kinds of hooks: __query parameters__ and __headers__.

Hook | Query Parameter |  Header | Valid for | Details
---- | --------------- |  ------ | --------- | -----------
status code | `?status=404` | `HTTP_MS_STATUS=404` | `GET /resources` | [see below](#status-code)
attributes | `?name=foo&description=bar` | `HTTP_ATTRIBUTES = name=foo;description=bar` | any | [see below](#attributes)
length | `?length=20` | `HTTP_MS_LENGTH=20` | `GET /resources` | [see below](#length)
errors | `?errors=name,description` | `HTTP_MS_ERRORS=name;description` | `POST /resources` | [see below](#errors)
disable fake data | `?fake=0` | `HTTP_MS_FAKE=0` | any | [see below](#fake)

#### status code
Returns the specified HTTP status code.

#### attributes
Overrides a resource's default defined data and any faked/generated data with the attribute(s) and value(s) specified.

#### length
Returns list of resources of specified `length`. If `length = 0`, returns an empty list.

#### errors
Returns a 400 response, and returns errors for the specified attributes (as though the submitted values for those fields caused validation errors).

#### fake
When set to `0`, or `false`, mock server won't return resources with faked/generated data, and will return the default defined data.


## Working on mock server

#### Installation

`pip install jsonapi-mock-server`

#### To add a new resource

Resources are defined in individual files in the `resources/` directory. These definitions are the only persistent data that mock server relies on.

To add a new resource:

##### Add resource data definitions
1. `cp resources/template.py resources/<your_resource_name>.py`
2. Open this file with your favorite editor.
3. Rename `ResourceNameResource` class to `<YourResourceName>Resource`.
4. Add a definition for `resource_type`.
   * This is the resource type that will be returned in the JsonAPI responses.
5. Add definitions for `attributes`.
   * These are the default attributes that will be returned for this resource in the JsonAPI responses.
6. Add definitions for `relationships`.
   * Relationships are defined as tuples, where the first element is the name of the related resource, and the second element are the related resource id(s).
   * To represent one-to-one or many-to-one relationships, the second element should be the related resource id value.
   * To represent many-to-many relationships, the second element should be a tuple of related resource ids. If you only want to define 0 or 1 related resource ids, this second element still needs to be a tuple (e.g. (1,) or tuple()) in order for mock server to return the correct many-to-many relationship object as defined by JsonAPI.

##### Add resource view
7. Rename `ResourceNameViewSet` class to `<YourResourceName>ViewSet`.
   * By default, `mock_server.base_views.ResourceViewSet` contains all list and detail resource actions. To only include one or the other, have your viewset inherit from `base_views.ResourceDetailViewSet` or `base_views.ResourceListViewSet`.

##### Register view in urls.py
8. Open `mock_server/urls.py` and register your new viewset.

##### Add relevant tests
9. `cp tests/template.py tests/tests_<underscored_singularized_resource_name>.py`
10. Open this file with your favorite editor. Rename all instances of `"Resource"` or `"resource"` with your resource name.
