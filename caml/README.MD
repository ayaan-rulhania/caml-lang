# Caml Language 🐪 

## 🎯 Mission

> To develop a programming language that makes learning coding and understanding it easier and simplified.  
> This language is meant to be more like English and readable for someone who does not know the language by heart. ❤️‍🔥

---

## ⚙️ Common Rules

| Rule | Description |
|------|--------------|
| Periods or “the”, “a”, and “an” | Can be added anywhere in code (ignored). |
| Case Sensitivity | Caml is **not case-sensitive**. |
| String Concatenation | Done using the `+` operator. |

---

## 💻 Display

| Syntax | Description |
|---------|-------------|
| `display 'hello'` | Logs `'hello'` to the console. |
| `interact "hello"` | Displays and takes input. |
| `{display/interact} plus bold` | Shows emphasis by darkening. |

---

## 💬 Comments

| Syntax | Type | Description |
|---------|------|-------------|
| `$ {comment here}` | Single-line | Normal comment |
| `$$$ {comment here} $$$` | Multi-line | Block comment |
| `{code} $ {comment here}` | Inline | Comment on the same line as code |

---

## 📊 Data Types

| Type | Description |
|-------|-------------|
| `string (str)` | Normal string |
| `integer (int)` | Integer within ±(2⁵³−1) |
| `float` | Decimal numbers |
| `null / undefined` | Unassigned variable |
| `boolean` | `true` or `false` |
| `list` | An array or list |
| `dictionary` | A key-value collection |
| `bigint` | Large integer beyond ±(2⁵³−1) |
| `image` | Generated or imported graphic |

---

## ⌨️ Keywords

| Keyword | Meaning |
|----------|----------|
| `and` | Two joined statements |
| `or` | Either condition true |
| `except` | Exception handling |

---

## ‼️ Operators

| Operator | Description | Supported Types |
|-----------|--------------|-----------------|
| `==` | Equality check | All |
| `!==` | Inequality check | All |
| `~` | Estimate (to 10 or 2 chars) | int, str |
| `~==` | Close estimate (to 1 or 1 char) | int, str |
| `is equal to` | Equality (natural language) | All |
| `is greater than` | Comparison | int, float |
| `is less than` | Comparison | int, float |

---

## 🟰 Variables

| Syntax | Description |
|---------|-------------|
| `Assign 'Tom' to boy` | Assigns `'Tom'` to variable |
| `Set variable boy to 'Tom'` | Same as above |
| `Block {var}` | Makes variable inaccessible |
| `Change {var} to {new}` | Updates variable |
| `Increase {var} by {num}` | Adds value *(int/float only)* |
| `Decrease {var} by {num}` | Subtracts value *(int/float only)* |
| `Multiply {var} by {num}` | Multiplies *(int/float only)* |
| `Divide {var} by {num}` | Divides *(int/float only)* |
| `Exponentiate {var} by {num}` | Raises to power *(int/float only)* |

---

## 📐 Math

| Syntax | Description |
|---------|-------------|
| `+ - / *` | Basic operations |
| `Generate random int (1 to 10)` | Random integer |
| `Square of n` | Returns n² |
| `Squareroot of n` | Returns √n |
| `num^num` | Exponentiation |
| `gcd(x, y)` | Greatest common divisor |
| `lcm(x, y)` | Least common multiple |

---

## 🧑‍💻 Functions

| Syntax | Description |
|---------|-------------|
| `Define function '____' which does:` | Defines a function (no args) |
| `Define function 'add' which takes (a, b) and does:` | Defines with arguments |
| `Call function 'add' with arguments (6, 7)` | Calls function |
| `Abbreviate function 'add' to 'a'` | Creates alias |

---

## 🤔 Conditionals

| Syntax | Description |
|---------|-------------|
| `If {statement}:` | Start conditional |
| `Or if {statement}:` | Else-if |
| `Otherwise:` | Else |

---

## ➰ Loops

| Syntax | Description |
|---------|-------------|
| `Repeat this n times:` | For fixed iteration |
| `Do this until {statement}:` | While loop |
| `For each {item} in {object} do:` | For-each loop |

---

## 📈 Graphics

| Syntax | Description |
|---------|-------------|
| `Draw a line measuring n {units}` | Draws a line |
| `Draw an angle measuring n°` | Draws an angle |
| `Graph the coordinates:` | Graphs points |
| `Draw a square/circle/triangle ...` | Draws shapes |

---

## 🔴 Getters

| Syntax | Description |
|---------|-------------|
| `Get length of {item}` | Returns length |
| `Get case of {item}` | Returns case format |
| `Get data type of {item}` | Returns data type |

---

## 📄 File Handling

| Syntax | Description |
|---------|-------------|
| `Create new file {file}` | Creates file |
| `Delete file {file}` | Deletes file (asks confirmation) |
| `Write {text} in file {file}` | Appends line |
| `Write {text} in file {file} at first line` | Inserts at top |
| `Find {text} in file {file} and replace with {text}` | Find & Replace |
| `Rename file {old} to {new}` | Rename file |
| `Access file {file}: {process}` | Chain file ops |

---

## 🧠 Modules

| Syntax | Description |
|---------|-------------|
| `Import {modules} from {filename.caml}` | Imports from another file |
| `Exports are {modules}` | Exports for import elsewhere |

---

## 📊 Lists / Arrays

| Syntax | Description |
|---------|-------------|
| `Create list {name} containing {a, b, c}` | Creates list |
| `Add {item} to list {name}` | Adds to list |
| `Remove {item} from list {name}` | Removes item |
| `Get {first/second/etc} item in list {name}` | Access item |

---

## 📚 Dictionaries

| Syntax | Description |
|---------|-------------|
| `Create dictionary {name} containing {key}:{value}` | Creates dictionary |
| `Add {key}:{value}` | Adds key-value pair |
| `Remove {key}:{value}` | Removes key-value |
| `Get {nth} item from dictionary {name}` | Access item |

---

## 🧊 Objects

| Syntax | Description |
|---------|-------------|
| `Create new object called Tom:` | Creates object |
| `Set Tom’s age to 5` | Adds property |
| `Change Tom’s age to 6` | Updates property |
| `Delete Tom’s birthday` | Removes property |
| `Block Tom’s password` | Hides property |
| `Add function which does: to Tom` | Adds method |

---

## 📱 GUI

### 🪟 Window

| Syntax | Description |
|---------|-------------|
| `Create window called Example:` | Creates window |
| `Set the title to "Hello"` | Sets title |
| `Set the background color to {color}` | Changes background |
| `Set the fontface to {Arial, Times, Roboto, System Default}` | Sets font |

### 🔘 Buttons

| Syntax | Description |
|---------|-------------|
| `Create a new button called Btn1:` | Creates button |
| `Display text "__" on button Btn1` | Adds text |
| `Set color of button Btn1 to "___"` | Sets button color |
| `$ same syntax as color of button for border/text/alignment` | Follows same pattern |

---

## ⚠️ Errors

> Coming soon...
