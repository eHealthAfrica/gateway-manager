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
