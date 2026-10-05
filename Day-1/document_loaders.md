# 📚 LlamaIndex — Document Loaders & Readers

> 🧭 **Learning Stage:** LlamaIndex Day 1 / Data Ingestion  
> 🎯 **Topic:** Document Loaders & Readers  
> 👨‍💻 **Level:** Beginner → Practical  
> 📌 **Scope:** This note covers **Document Loaders and Readers only**.  
> 🚫 We intentionally do **not** go into chunking, embeddings, indexing, retrieval, or LLM generation here.

---

# 🗺️ Table of Contents

1. [🌟 What Are Document Loaders?](#-1-what-are-document-loaders)
2. [🤔 Why Do We Need Loaders?](#-2-why-do-we-need-loaders)
3. [🧠 The Core Mental Model](#-3-the-core-mental-model)
4. [🏗️ Where Loaders Fit in LlamaIndex](#-4-where-loaders-fit-in-llamaindex)
5. [📦 Readers vs Loaders](#-5-readers-vs-loaders)
6. [🔍 Exploring the `readers` Module](#-6-exploring-the-readers-module)
7. [📋 The 5 Public Items We Found](#-7-the-5-public-items-we-found)
8. [1️⃣ `SimpleDirectoryReader`](#1-simpledirectoryreader)
9. [2️⃣ `FileSystemReaderMixin`](#2-filesystemreadermixin)
10. [3️⃣ `ReaderConfig`](#3-readerconfig)
11. [4️⃣ `Document`](#4-document)
12. [5️⃣ `StringIterableReader`](#5-stringiterablereader)
13. [📄 Specialized File Readers](#-13-specialized-file-readers)
14. [📕 PDF — `PyMuPDFReader`](#-14-pdf--pymupdfreader)
15. [📝 TXT Files](#-15-txt-files)
16. [📊 CSV Files](#-16-csv-files)
17. [📘 DOCX Files](#-17-docx-files)
18. [🧾 JSON Files](#-18-json-files)
19. [🌐 Web Pages](#-19-web-pages)
20. [🔌 API / Database / Cloud Data](#-20-api--database--cloud-data)
21. [🎯 `SimpleDirectoryReader` vs Specialized Readers](#-21-simpledirectoryreader-vs-specialized-readers)
22. [🔄 Complete Loader Flow](#-22-complete-loader-flow)
23. [🧪 Practical Examples](#-23-practical-examples)
24. [⚠️ Important Things to Remember](#-24-important-things-to-remember)
25. [🧠 Quick Revision](#-25-quick-revision)
26. [🎤 Tricky Oral Questions](#-26-tricky-oral-questions)
27. [🏁 Final Mental Model](#-27-final-mental-model)

---

# 🌟 1. What Are Document Loaders?

A **Document Loader / Reader** is responsible for taking data from an external source and bringing it into LlamaIndex.

Think of it as the **entry gate** of our data.

```text
🌍 External Data
      ↓
📥 Loader / Reader
      ↓
📄 LlamaIndex Documents
```

### Examples of external data

- 📕 PDF
- 📝 TXT
- 📊 CSV
- 📘 DOCX
- 🧾 JSON
- 🌐 Web pages
- 📁 Directories
- 🗄️ Databases
- 🔌 APIs
- ☁️ Cloud storage
- 📝 Python strings

---

# 🤔 2. Why Do We Need Loaders?

Different data sources have different formats.

For example:

```text
📕 PDF
   → has pages and PDF structure

📊 CSV
   → has rows and columns

📘 DOCX
   → has Word document structure

🌐 HTML
   → has web-page structure

🧾 JSON
   → has structured key/value data
```

So we cannot assume that every source can be read in exactly the same way.

That's why LlamaIndex provides different **readers/loaders**.

### Simple example

```text
sample.pdf
    ↓
PyMuPDFReader
    ↓
Documents
```

While:

```text
company_data/
    ↓
SimpleDirectoryReader
    ↓
Documents
```

---

# 🧠 3. The Core Mental Model

The most important thing to remember:

```text
SOURCE
   ↓
READER / LOADER
   ↓
DOCUMENT
```

### Example 1 — PDF

```text
📕 report.pdf
      ↓
📖 PyMuPDFReader
      ↓
📄 Document
```

### Example 2 — Directory

```text
📁 company_data/
      ↓
📖 SimpleDirectoryReader
      ↓
📄 Documents
```

### Example 3 — Python strings

```text
📝 ["Hello", "Python", "LlamaIndex"]
              ↓
     StringIterableReader
              ↓
          Documents
```

---

# 🏗️ 4. Where Loaders Fit in LlamaIndex

At a very high level, LlamaIndex works like this:

```text
┌─────────────────────────────┐
│        🌍 DATA SOURCES      │
│ PDF / CSV / DOCX / Web / DB │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│      📥 LOADERS / READERS   │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│         📄 DOCUMENTS        │
└──────────────┬──────────────┘
               ↓
       ⬇️ Later stages ⬇️
   Nodes → Embeddings → Index
```

### 🚨 Important

For this topic, our responsibility ends here:

```text
DATA
  ↓
LOADER
  ↓
DOCUMENTS
```

We are **not** discussing what happens after Documents yet.

---

# 📦 5. Readers vs Loaders

You will see both words:

- **Reader**
- **Loader**

They are often used to describe the same general idea:

> Something that reads external data and converts it into data that LlamaIndex can use.

For example:

```python
from llama_index.readers.file import PyMuPDFReader
```

The class is called a **Reader**.

But conceptually, we can say:

> "We use a PDF loader."

So don't get confused just because LlamaIndex uses the word **Reader** in class/module names.

---

# 🔍 6. Exploring the `readers` Module

One important thing we explored was the LlamaIndex `readers` module.

We found an `__all__` definition similar to:

```python
__all__ = [
    "SimpleDirectoryReader",
    "FileSystemReaderMixin",
    "ReaderConfig",
    "Document",
    "StringIterableReader",
]
```

This was important because it showed us what the module exposes as its **public API**.

---

# 🧩 What is `__all__`?

`__all__` is a Python convention used to define names that should be considered public when using wildcard imports.

Example:

```python
__all__ = [
    "SimpleDirectoryReader",
    "Document",
]
```

This tells Python:

> These are the names intended to be publicly exposed from this module.

### ⚠️ Important

`__all__` does **not** mean:

> "Every item listed here is a document loader."

The list can contain supporting classes and objects too.

That distinction was important in our exploration.

---

# 📋 7. The 5 Public Items We Found

Here is the exact mental classification we discussed:

| # | Name | What it is | Main purpose |
|---|---|---|---|
| 1️⃣ | `SimpleDirectoryReader` | Reader | 📁 Reads supported local files/directories |
| 2️⃣ | `FileSystemReaderMixin` | Mixin | 🛠️ Reusable filesystem-related functionality |
| 3️⃣ | `ReaderConfig` | Configuration/support class | ⚙️ Reader configuration |
| 4️⃣ | `Document` | Data object | 📄 Represents loaded content |
| 5️⃣ | `StringIterableReader` | Reader | 📝 Reads strings from an iterable |

### ⭐ Important observation

The five names are **not five different loader types**.

For example:

```text
SimpleDirectoryReader  → actual reader
StringIterableReader   → actual reader

FileSystemReaderMixin  → supporting mixin
ReaderConfig            → supporting configuration
Document                → data representation
```

This is an important distinction.

---

# 1️⃣ `SimpleDirectoryReader`

## 🎯 What is it?

`SimpleDirectoryReader` is a high-level reader used to load supported files from a local directory.

### Import

```python
from llama_index.core import SimpleDirectoryReader
```

### Basic code

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader(
    "./data"
).load_data()

print("Documents:", len(documents))
```

### Flow

```text
📁 data/
   ├── report.pdf
   ├── notes.txt
   ├── employees.csv
   └── policy.docx
          ↓
📖 SimpleDirectoryReader
          ↓
📄 Documents
```

---

## 📌 Why is it called `SimpleDirectoryReader`?

Because its main purpose is simple:

> Give it a directory → it reads supported files from that directory.

You don't have to manually create a separate loading operation for every supported local file.

---

## 📄 Loading a single file

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader(
    input_files=["report.pdf"]
).load_data()

print("Documents:", len(documents))
```

---

## 📁 Loading recursively

Suppose:

```text
data/
├── report.pdf
└── technical/
    ├── api.txt
    └── database.txt
```

You can enable recursive loading:

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader(
    input_dir="./data",
    recursive=True
).load_data()

print("Documents:", len(documents))
```

---

# 2️⃣ `FileSystemReaderMixin`

## 🤔 What is a Mixin?

A **mixin** is a reusable class that provides functionality to other classes.

It is usually not something a beginner needs to instantiate directly.

Think:

```text
FileSystemReaderMixin
        ↓
Reusable filesystem functionality
        ↓
Used by reader classes
```

### 🧠 Easy memory trick

```text
Reader        → "I read the data."

Mixin         → "I provide reusable functionality."

Document      → "I represent the data."

Config        → "I configure the reader."
```

So:

> `FileSystemReaderMixin` is **not a normal standalone loader that you usually call directly**.

---

# 3️⃣ `ReaderConfig`

## ⚙️ What is it?

`ReaderConfig` is related to configuration/support for readers.

Think:

```text
Reader
  +
ReaderConfig
  ↓
Configured reading behavior
```

It is not the same thing as a PDF reader or directory reader.

### 🧠 Easy memory trick

```text
ReaderConfig = configuration
```

---

# 4️⃣ `Document`

## 📄 What is a Document?

`Document` represents content that has been loaded into LlamaIndex.

Example:

```python
from llama_index.core import Document

document = Document(
    text="Python is a programming language."
)

print(document.text)
```

Output:

```text
Python is a programming language.
```

### Important distinction

`Document` is **not a loader**.

It is the object that represents the loaded data.

```text
Loader
   ↓
Document
```

For example:

```text
📕 PDF
 ↓
PyMuPDFReader
 ↓
📄 Document
```

---

# 5️⃣ `StringIterableReader`

## 📝 What is it?

`StringIterableReader` is useful when your source is already an iterable of strings.

For example:

```python
texts = [
    "Python is a programming language.",
    "FastAPI is a Python framework.",
    "LlamaIndex is an AI data framework."
]
```

Instead of reading a physical file, we already have the text in Python.

### Import

```python
from llama_index.core.readers import StringIterableReader
```

### Simple example

```python
from llama_index.core.readers import StringIterableReader

texts = [
    "Python is a programming language.",
    "FastAPI is a Python framework."
]

reader = StringIterableReader()

documents = reader.load_data(texts)

print("Documents:", len(documents))

for document in documents:
    print(document.text)
```

### Flow

```text
📝 Python strings
       ↓
StringIterableReader
       ↓
📄 Documents
```

---

# 📄 13. Specialized File Readers

Now we can connect the general reader idea to specific file types.

Common examples:

```text
📕 PDF
    ↓
PyMuPDFReader

📘 DOCX
    ↓
DocxReader

📝 TXT
    ↓
SimpleDirectoryReader / supported file reader

📊 CSV
    ↓
SimpleDirectoryReader / CSV-specific reader

🌐 Web page
    ↓
Web reader
```

### The key idea

Some sources have dedicated readers.

Others can be handled conveniently through `SimpleDirectoryReader`.

---

# 📕 14. PDF — `PyMuPDFReader`

PDF is one of the most important specialized examples.

### Import

```python
from llama_index.readers.file import PyMuPDFReader
```

### Code

```python
from llama_index.readers.file import PyMuPDFReader

reader = PyMuPDFReader()

documents = reader.load_data(
    file_path="sample.pdf"
)

print("Documents:", len(documents))
```

### Flow

```text
📕 sample.pdf
      ↓
📖 PyMuPDFReader
      ↓
📄 Documents
```

### Why use it?

Because `PyMuPDFReader` is specifically designed to extract content from PDF files using the PyMuPDF ecosystem.

---

# 📝 15. TXT Files

TXT is plain text.

Example:

```text
data/
└── notes.txt
```

A simple local-file approach is:

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader(
    "./data"
).load_data()

for document in documents:
    print(document.text)
```

### Flow

```text
📝 notes.txt
     ↓
SimpleDirectoryReader
     ↓
📄 Document
```

---

# 📊 16. CSV Files

CSV means:

> **Comma-Separated Values**

Example:

```csv
name,department
Alice,IT
Bob,HR
Charlie,Finance
```

A simple local-file example:

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader(
    "./data"
).load_data()

for document in documents:
    print(document.text)
```

### Flow

```text
📊 employees.csv
       ↓
CSV reading support
       ↓
📄 Document
```

### ⚠️ Important

CSV is structured data.

For complex applications, you may want more control over how rows/columns become text or metadata. A specialized reader or custom preprocessing may be more appropriate.

---

# 📘 17. DOCX Files

DOCX is the Microsoft Word document format.

A specialized reader can be used.

### Example import

```python
from llama_index.readers.file import DocxReader
```

### Example

```python
from llama_index.readers.file import DocxReader

reader = DocxReader()

documents = reader.load_data(
    file_path="company_policy.docx"
)

print("Documents:", len(documents))
```

### Flow

```text
📘 company_policy.docx
          ↓
     DocxReader
          ↓
      📄 Documents
```

> ⚠️ Exact reader availability and import paths can depend on the installed LlamaIndex reader package/version.

---

# 🧾 18. JSON Files

JSON is structured data.

Example:

```json
{
    "name": "Alice",
    "department": "IT",
    "experience": 3
}
```

The general idea is:

```text
🧾 JSON
  ↓
JSON reader / supported file reader
  ↓
📄 Document
```

For simple local files, supported readers may be able to load the file.

For complex JSON structures, you may want to decide exactly how the fields should be represented.

For example:

```text
name       → Alice
department → IT
experience → 3
```

could be transformed into meaningful document text.

---

# 🌐 19. Web Pages

A web page is not a local file.

Example:

```text
https://example.com
```

The conceptual flow is:

```text
🌐 URL
 ↓
Web Reader
 ↓
📄 Documents
```

Web readers are designed to fetch/read web content.

The exact reader and import depend on the LlamaIndex web reader integration being used.

---

# 🔌 20. API / Database / Cloud Data

LlamaIndex is not limited to files.

You may also bring data from:

### 🗄️ Database

```text
Database
   ↓
Database integration
   ↓
Documents / data
```

### 🔌 API

```text
External API
   ↓
API integration / custom reader
   ↓
Documents / data
```

### ☁️ Cloud storage

```text
Cloud Storage
   ↓
Cloud integration
   ↓
Documents / data
```

The exact integration depends on the source.

The general mental model remains:

```text
External Source
      ↓
Reader / Integration
      ↓
LlamaIndex Documents
```

---

# 🎯 21. `SimpleDirectoryReader` vs Specialized Readers

This is a very important interview/practical distinction.

## 📁 `SimpleDirectoryReader`

Use it when you want a convenient way to load supported local files.

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader(
    "./data"
).load_data()
```

Think:

```text
"Here is my directory.
Read the supported files inside it."
```

---

## 📕 Specialized Reader

Use a specialized reader when you specifically want a reader for a particular source.

Example:

```python
from llama_index.readers.file import PyMuPDFReader

reader = PyMuPDFReader()

documents = reader.load_data(
    file_path="sample.pdf"
)
```

Think:

```text
"I specifically want to read this PDF."
```

---

## 🧠 Easy Comparison

| `SimpleDirectoryReader` | Specialized Reader |
|---|---|
| 📁 High-level | 🎯 Specific |
| Works with supported local files | Designed for a particular source/type |
| Convenient | More explicit |
| Example: directory | Example: `PyMuPDFReader` |
| Good default for many local-file cases | Useful when you specifically need that reader |

---

# 🔄 22. Complete Loader Flow

Here is the complete picture for everything covered in this topic:

```text
                    🌍 DATA SOURCES
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ↓                 ↓                 ↓
     📕 PDF             📊 CSV            📘 DOCX
        │                 │                 │
        ↓                 ↓                 ↓
 PyMuPDFReader      File Reader        DocxReader
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ↓
                     📄 DOCUMENTS
```

Another source:

```text
📁 DIRECTORY
     ↓
SimpleDirectoryReader
     ↓
📄 Documents
```

And:

```text
📝 Python Strings
     ↓
StringIterableReader
     ↓
📄 Documents
```

---

# 🧪 23. Practical Examples

## Example 1 — Directory

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader(
    "./data"
).load_data()

print("Documents:", len(documents))
```

---

## Example 2 — PDF

```python
from llama_index.readers.file import PyMuPDFReader

reader = PyMuPDFReader()

documents = reader.load_data(
    file_path="sample.pdf"
)

print("Documents:", len(documents))
```

---

## Example 3 — Strings

```python
from llama_index.core.readers import StringIterableReader

texts = [
    "Python is easy to learn.",
    "LlamaIndex works with LLM applications."
]

reader = StringIterableReader()

documents = reader.load_data(texts)

for document in documents:
    print(document.text)
```

---

## Example 4 — Inspecting loaded documents

Once documents are loaded, you can inspect their text:

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader(
    "./data"
).load_data()

for document in documents:
    print("----- DOCUMENT -----")
    print(document.text)
```

This is useful for understanding:

> **What exactly did my loader read?**

---

# ⚠️ 24. Important Things to Remember

### 1️⃣ Loader ≠ Document

```text
Loader
  ↓
reads data

Document
  ↓
represents loaded data
```

---

### 2️⃣ `__all__` does not mean "all loaders"

Our discovered list:

```python
__all__ = [
    "SimpleDirectoryReader",
    "FileSystemReaderMixin",
    "ReaderConfig",
    "Document",
    "StringIterableReader",
]
```

contains readers **and supporting/public objects**.

---

### 3️⃣ `FileSystemReaderMixin` is not a normal loader

It is a reusable mixin for filesystem-related functionality.

---

### 4️⃣ `ReaderConfig` is configuration-related

It helps represent reader configuration/support.

---

### 5️⃣ `Document` is not a reader

It represents the loaded content.

---

### 6️⃣ `StringIterableReader` does not need a physical file

It can work with strings already present in Python.

---

### 7️⃣ `SimpleDirectoryReader` is high-level

It is useful when you have a directory containing supported local files.

---

### 8️⃣ Specialized readers exist

Example:

```text
PDF → PyMuPDFReader
DOCX → DocxReader
```

---

### 9️⃣ Exact reader packages can vary

LlamaIndex is modular.

Some readers are provided by separate reader/integration packages, and exact imports can depend on the installed version.

So if an import fails:

```text
❌ ImportError
```

don't immediately assume the reader doesn't exist.

Check the appropriate installed LlamaIndex reader package/version.

---

# 🧠 25. Quick Revision

## ⭐ What is a Document Loader?

> A component that reads external data and brings it into LlamaIndex.

---

## ⭐ Why do we need loaders?

> Because different data sources have different formats and reading requirements.

---

## ⭐ Main mental model

```text
SOURCE
   ↓
READER / LOADER
   ↓
DOCUMENT
```

---

## ⭐ Important readers/objects we explored

```text
📁 SimpleDirectoryReader
🛠️ FileSystemReaderMixin
⚙️ ReaderConfig
📄 Document
📝 StringIterableReader
```

Remember:

> These five are **not five loader types**.

---

## ⭐ Specialized examples

```text
📕 PDF
 ↓
PyMuPDFReader

📘 DOCX
 ↓
DocxReader
```

---

## ⭐ `SimpleDirectoryReader`

```text
Directory
   ↓
SimpleDirectoryReader
   ↓
Documents
```

---

## ⭐ `StringIterableReader`

```text
Python strings
   ↓
StringIterableReader
   ↓
Documents
```

---

# 🎤 26. Tricky Oral Questions

These are good questions to test whether you really understand the topic.

### 🟢 Q1

**If I have a PDF, why can't I simply say "Document" and skip the reader?**

👉 Because `Document` represents the loaded content. Something still needs to read/extract the content from the PDF.

---

### 🟢 Q2

**Is `Document` a loader?**

👉 No. `Document` is a data representation of loaded content.

---

### 🟡 Q3

**Does `__all__` contain only loaders?**

👉 No. It can expose readers as well as supporting/public classes and objects.

---

### 🟡 Q4

**Which two items from our `__all__` list are actual reader classes?**

👉 `SimpleDirectoryReader` and `StringIterableReader`.

---

### 🟡 Q5

**Then what is `FileSystemReaderMixin`?**

👉 A reusable mixin that provides filesystem-related functionality to reader classes.

---

### 🟡 Q6

**What is `ReaderConfig`?**

👉 It is related to reader configuration/support rather than being a data-source reader itself.

---

### 🔴 Q7

**If `SimpleDirectoryReader` can read PDFs, why would I use `PyMuPDFReader`?**

👉 `SimpleDirectoryReader` is a high-level convenient reader for supported local files. `PyMuPDFReader` is a specialized reader explicitly designed for PDF reading.

---

### 🔴 Q8

**Does every file extension require a completely separate reader?**

👉 No. `SimpleDirectoryReader` can handle multiple supported local file types. Specialized readers are available for particular formats or use cases.

---

### 🔴 Q9

**Can a loader create embeddings?**

👉 Loading and embedding are separate responsibilities. The loader's job is to load the source into LlamaIndex documents.

---

### 🔴 Q10

**Can `StringIterableReader` read a PDF?**

👉 No. Its purpose is to read strings from an iterable, not PDF files.

---

### 🔴 Q11

**What is the difference between a Reader and a Document?**

👉

```text
Reader   → reads
Document → represents
```

---

### 🔴 Q12

**What is the first question you should ask when choosing a loader?**

👉

> **"What is my data source?"**

Then:

```text
What is my source?
       ↓
Which reader understands it?
       ↓
Load it
       ↓
Get Documents
```

---

# 🏁 27. Final Mental Model

If you remember only one diagram from this entire topic, remember this:

```text
                    🌍 YOUR DATA
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ↓                 ↓                 ↓
     📕 PDF             📁 Files          📝 Strings
       │                 │                 │
       ↓                 ↓                 ↓
PyMuPDFReader    SimpleDirectoryReader   StringIterableReader
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ↓
                    📄 DOCUMENTS
                         │
                         ↓
              ⏭️ NEXT LlamaIndex STAGES
```

---

# 💡 The One Sentence to Remember

> **Document Loaders are the entry point that reads data from different sources and brings that data into LlamaIndex as Documents.**

### 🧠 And the easiest memory formula:

```text
🌍 SOURCE
   +
📖 READER
   ↓
📄 DOCUMENT
```

---

## 📝 End of Topic

✅ What Document Loaders are  
✅ Why they are needed  
✅ Reader vs Loader  
✅ `__all__`  
✅ The 5 public items from the readers module  
✅ `SimpleDirectoryReader`  
✅ `FileSystemReaderMixin`  
✅ `ReaderConfig`  
✅ `Document`  
✅ `StringIterableReader`  
✅ PDF / `PyMuPDFReader`  
✅ TXT  
✅ CSV  
✅ DOCX  
✅ JSON  
✅ Web  
✅ API / Database / Cloud sources  
✅ Simple vs Specialized Readers  
✅ Practical code  
✅ Mental models  
✅ Tricky oral questions

**🎯 Document Loaders — COMPLETE**
