# py2aqa32

Python Compiler to AQA Assembly as implemented by Peter Higginson at [https://www.peterhigginson.co.uk/AQA/](https://www.peterhigginson.co.uk/AQA/).

`main` branch should compile accurately but not optimally the code in `test_code.py`.

The official instruction set is found [here](https://filestore.aqa.org.uk/resources/computing/AQA-75162-75172-ALI.PDF).
This compiler aims to run on the Peter Higginson simulator as documented [here](https://www.peterhigginson.co.uk/AQA/info.html). Note that he has expanded upon it to make a working simulation - if they ever differ the Higginson version is preferred.

## Supported Syntax

`test_code.py` contains an example of every supported Python construction, but not every permutation.

Unsupported syntax is ignored and no error is raised.

- Integer variables only (PH treats them as signed).
- Assignment (of the forms a = b and a += b).
- Integer Addition and Subtraction - but the result must be assigned to a variable.
- Comparisions - but the result must be used in a condition.
- While loops - those of the form "while False" are optimised out.
- if/elif/else - as above.
- Comments - this is a consequence of using the `ast` Python parser in the stdlib.

[`TODO.md`](TODO.md) contains plans and discussions for remaining syntax and constructions.
