# Solution

A solution gathers a set of services.

The expected format for each solution file is:

```javascript
{
  // service name (unique among rest of solutions)
  "name": "solution-name",
  "services": [
    // each of these services must have its definition file in the "service" folder
    "service-name-1",
    ...,
    "service-name-n"
  ]
}
```

To add a solution to an existing realm in Kong

```bash
docker-compose -f docker-compose-generation.yml run auth add_solution "solution-name" "realm-name"
```

To remove a solution from an existing realm in Kong

```bash
docker-compose -f docker-compose-generation.yml run auth remove_solution "solution-name" "realm-name"
```

To remove a solution from ALL existing realms in Kong

```bash
docker-compose -f docker-compose-generation.yml run auth remove_solution "solution-name" "*"
```
