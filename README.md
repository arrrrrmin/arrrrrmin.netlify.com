# arrrrrmin.netlify.com

My very small thinking, working, developing, region of interest bubble. Build with [hugo](https://gohugo.io), styling based on [PaperMod](https://github.com/adityatelange/hugo-PaperMod).

* [content/](content/) contains posts and pages. Where [content/posts/](content/posts/) are generated by executing [code/python-examples/build.py](code/python-examples/build.py). 
* [code/python-examples/](code/python-examples/) contains code for posts. These are referenced in markdown using [mdx-include](https://github.com/neurobin/mdx_include). 
* Each post file in [code/python-examples/python_examples/](code/python-examples/python_examples/) runs as is and can be linted using a `tool.poe.tasks` with `poe run lint`. But be aware that linting cannot changes the lines of code one has referenced in md before.
* Deploy by commit to `main`, build is done by [netlify](https://www.netlify.com).

