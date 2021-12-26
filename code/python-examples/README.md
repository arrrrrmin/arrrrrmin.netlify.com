# Python Examples

This is a small subdirectory (poetry project) containing code snippets, examples used in
blog articles. Code is fully or partially included with 
[`mdx-include`](https://github.com/neurobin/mdx_include). Like this one can have IDE 
linting and sentiy checks when writing code blocks for blog articles and ensure that 
blocks run '*as they are*'. 

## How it works:
* Run `hugo serve` from `arrrrrmin.netlify.com/`
* Edit article sources in `code/python-examples/<article_name>/README.md`
* In a new tab  run `poetry run poe build-md` from `code/python-examples/`
* View the result
