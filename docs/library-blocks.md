# Embedded library-block definitions

xml2st transpiles FBD/LD to Structured Text. For **function** blocks it emits a
local temporary per output (`_TMP_<TYPE><id>_OUT`), and that temporary needs a
concrete declared type. xml2st infers the type from the wired connections, but
when it cannot — e.g. a **nullary** function (`CURRENT_DT`) whose output is
unconnected — it falls back to the illegal type `ANY`, which the downstream
compiler (STruC++) rejects.

To stay **library-agnostic**, xml2st does not bundle block signatures. Instead,
the upstream tool (openplc-editor / openplc-web) embeds the signatures of every
block the project uses directly in the project's PLCopen XML. Everything xml2st
needs to transpile the project travels inside the project file. xml2st knows
nothing about STruC++, `.stlib`, or any external library.

> Function **blocks** never need this (they are declared by instance/type name
> and emit no `_TMP`), but embedding their output types lets xml2st resolve
> *other* blocks' generic outputs that are fed by an FB output.

## Where the payload lives

A single project-level `<addData>` entry — the PLCopen TC6 vendor-extension
point, which is schema-valid and accepted by xml2st's strict parser without any
schema change:

```xml
<project>
  ...
  <instances> ... </instances>
  <addData>
    <data name="openplc.org/xml2st/library-blocks" handleUnknown="discard">
      <libraryBlocks>
        <!-- one <pou> per library block the project references -->
        <pou name="CURRENT_DT" pouType="function">
          <interface>
            <returnType><DT/></returnType>
          </interface>
        </pou>

        <pou name="ADD" pouType="function" extensible="true">
          <interface>
            <returnType><ANY_NUM/></returnType>
            <inputVars>
              <variable name="IN1"><type><ANY_NUM/></type></variable>
              <variable name="IN2"><type><ANY_NUM/></type></variable>
            </inputVars>
          </interface>
        </pou>

        <pou name="TON" pouType="functionBlock">
          <interface>
            <inputVars>
              <variable name="IN"><type><BOOL/></type></variable>
              <variable name="PT"><type><TIME/></type></variable>
            </inputVars>
            <outputVars>
              <variable name="Q"><type><BOOL/></type></variable>
              <variable name="ET"><type><TIME/></type></variable>
            </outputVars>
          </interface>
        </pou>
      </libraryBlocks>
    </data>
  </addData>
</project>
```

## Format rules

- **Container:** `addData/data[@name="openplc.org/xml2st/library-blocks"]/libraryBlocks`.
  `handleUnknown="discard"` is recommended (the data is advisory).
- **One `<pou>` per used block type**, deduplicated. Emit only blocks that come
  from a library; user-defined POUs are already in `<types><pous>` and need no
  entry.
- **`pouType`** is `function` or `functionBlock`.
- **Interface** uses standard PLCopen elements: `<returnType>`, `<inputVars>`,
  `<outputVars>`, `<inOutVars>`, each `<variable>` carrying a `<type>`.
  - A base type is the element tag (`<INT/>`, `<DT/>`, `<ANY_NUM/>`); a derived
    type is `<derived name="MyType"/>`.
  - **Keep IEC meta-types verbatim** (`ANY`, `ANY_NUM`, `ANY_ELEMENTARY`, …).
    xml2st resolves them from the wired connections; you do not need to
    monomorphize per call site. One `ADD : (ANY_NUM, ANY_NUM) -> ANY_NUM`
    suffices for INT, REAL, etc.
- **Variadic / extensible** functions (`ADD`, `AND`, `OR`, `MUL`, `MUX`, …)
  carry `extensible="true"` on the `<pou>` and declare their base inputs
  (`IN1`, `IN2`). xml2st emits all the inputs actually wired on each instance.
- **Bodies are omitted** — these are signatures, not code. xml2st registers them
  as a block library; it never emits ST definitions for them.

## How xml2st consumes it

`plcopen/library_blocks.extract_library_blocks()` parses the payload leniently
(it never blocks the main strict load), and `PLCControler.RegisterLibraryBlocks()`
registers each definition so `GetBlockType()` resolves it during transpilation.
Blocks absent from the payload still degrade gracefully to permissive synthesis.
