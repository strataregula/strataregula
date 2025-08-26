# StrataRegula System Architecture - UML Diagrams

## Component Diagram: Overall System Architecture

```plantuml
@startuml StrataRegula_Component_Architecture

!define RECTANGLE class

package "VS Code Environment" {
    RECTANGLE "Extension\n(extension.ts)" as Extension {
        +activate()
        +registerCommands()
        +startLanguageServer()
    }
    
    RECTANGLE "Preview Provider\n(previewProvider.ts)" as PreviewProvider {
        +showPatternPreview()
        +updatePreview()
        +renderWebView()
    }
    
    RECTANGLE "Pattern Expander\n(patternExpander.ts)" as VSPatternExpander {
        +expandPattern()
        +getExpansionCount()
        +getPatternSuggestions()
    }
}

package "Language Server Process (LSP)" {
    RECTANGLE "LSP Server\n(server.ts)" as LSPServer {
        +onCompletion()
        +onHover()
        +onValidation()
        +handleDocumentChange()
    }
    
    RECTANGLE "YAML Analyzer\n(yamlAnalyzer.ts)" as YAMLAnalyzer {
        +analyzeDocument()
        +extractPatternsFromYaml()
        +learnPatternFromKey()
        +buildConfigFromLearning()
    }
    
    RECTANGLE "Pattern Provider\n(patternProvider.ts)" as PatternProvider {
        +provideCompletions()
        +generateCompletions()
        +createEnvironmentCompletions()
        +createServiceCompletions()
    }
    
    RECTANGLE "Pattern Tokenizer\n(patternTokenizer.ts)" as PatternTokenizer {
        +parsePatternContext()
        +tokenizePattern()
        +getPatternDepth()
    }
}

package "Python Core Engine" {
    RECTANGLE "Configuration Engine\n(config.py)" as ConfigEngine {
        +load_config()
        +compile_patterns()
        +validate_syntax()
    }
    
    RECTANGLE "Pattern Expander\n(pattern_expander.py)" as PythonPatternExpander {
        +expand_pattern()
        +compile_to_static_mapping()
        +get_fingerprint()
    }
    
    RECTANGLE "Compile Command\n(compile_command.py)" as CompileCommand {
        +dump_compiled_config()
        +format_tree_output()
        +build_pattern_tree()
    }
}

package "Shared Data Layer" {
    RECTANGLE "Learned Patterns\n(Database)" as LearnedPatterns {
        +pattern: string
        +frequency: number
        +context: string
        +lastSeen: Date
    }
    
    RECTANGLE "Dynamic Hierarchy\n(Configuration)" as DynamicHierarchy {
        +environments: Set<string>
        +services: Set<string>
        +configTypes: Set<string>
        +patterns: Map<string, LearnedPattern>
    }
}

' Relationships
Extension --> PreviewProvider : uses
Extension --> VSPatternExpander : initializes
Extension --> LSPServer : starts via IPC

LSPServer --> YAMLAnalyzer : delegates analysis
LSPServer --> PatternProvider : requests completions
PatternProvider --> PatternTokenizer : parses context

YAMLAnalyzer --> LearnedPatterns : stores/retrieves
YAMLAnalyzer --> DynamicHierarchy : builds

VSPatternExpander --> DynamicHierarchy : reads config
PythonPatternExpander --> ConfigEngine : integrates with

CompileCommand --> PythonPatternExpander : uses for dump
ConfigEngine --> LearnedPatterns : shared patterns

@enduml
```

## Sequence Diagram: Dynamic Pattern Learning Flow

```plantuml
@startuml Pattern_Learning_Sequence

actor User
participant "VS Code" as VSCode
participant "Extension" as Ext
participant "Language Server" as LSP
participant "YAML Analyzer" as Analyzer
participant "Learned Patterns\nDatabase" as DB
participant "Pattern Provider" as Provider

User -> VSCode : Opens YAML file
VSCode -> Ext : File opened event
Ext -> LSP : Document opened notification

LSP -> Analyzer : analyzeDocument(document)
activate Analyzer

Analyzer -> Analyzer : yaml.load(content)
Analyzer -> Analyzer : extractPatternsFromYaml(yamlData)

loop For each key in YAML
    Analyzer -> Analyzer : isStrataRegulaPattern(key)
    alt Valid pattern found
        Analyzer -> Analyzer : learnPatternFromKey(pattern)
        Analyzer -> DB : Update pattern frequency
        Analyzer -> DB : Store pattern metadata
    end
end

Analyzer -> Analyzer : buildConfigFromLearning()
Analyzer --> LSP : StrataRegulaConfig
deactivate Analyzer

LSP -> Provider : updateConfig(config)
LSP --> Ext : Configuration updated
Ext --> VSCode : Ready for completions

note right of DB
    Patterns stored with:
    - Frequency count
    - Last seen timestamp
    - Context information
    - Hierarchical position
end note

@enduml
```

## Sequence Diagram: IntelliSense Completion Flow

```plantuml
@startuml IntelliSense_Completion_Flow

actor User
participant "VS Code\nEditor" as Editor
participant "Extension" as Ext
participant "Language Server" as LSP
participant "Pattern Provider" as Provider
participant "Pattern Tokenizer" as Tokenizer
participant "Learned Patterns\nDatabase" as DB

User -> Editor : Types "prod."
Editor -> Ext : Completion request

Ext -> LSP : textDocument/completion
activate LSP

LSP -> Provider : provideCompletions(document, position)
activate Provider

Provider -> Provider : isInValuePosition(textBeforeCursor)
Provider -> Tokenizer : parsePatternContext(textBeforeCursor)
activate Tokenizer

Tokenizer -> Tokenizer : Analyze pattern depth
Tokenizer -> Tokenizer : Extract current pattern
Tokenizer --> Provider : PatternContext{depth: 1, currentPattern: "prod"}
deactivate Tokenizer

Provider -> DB : Query learned services for "prod"
DB --> Provider : ["frontend", "backend", "api", "worker"]

Provider -> Provider : generateCompletions(context)

alt Depth = 1 (Services)
    Provider -> Provider : createServiceCompletions()
    Provider -> Provider : Add wildcard option
else Depth = 2 (Config Types)
    Provider -> Provider : createConfigTypeCompletions()
else Advanced
    Provider -> Provider : createAdvancedCompletions()
end

Provider --> LSP : CompletionItem[]
deactivate Provider

LSP --> Ext : Completion response
deactivate LSP

Ext --> Editor : Display completions
Editor --> User : Shows intelligent suggestions

@enduml
```

## Class Diagram: Core Data Structures

```plantuml
@startuml Core_Data_Structures

interface LearnedPattern {
    +pattern: string
    +frequency: number
    +context: string
    +lastSeen: Date
}

class DynamicHierarchy {
    +environments: Set<string>
    +services: Set<string>
    +configTypes: Set<string>
    +patterns: Map<string, LearnedPattern>
    
    +addEnvironment(env: string): void
    +addService(service: string): void
    +addConfigType(type: string): void
    +updatePattern(pattern: LearnedPattern): void
}

class StrataRegulaConfig {
    +hierarchy: HierarchyConfig
    +completionSettings: CompletionSettings
    +learnedPatterns?: LearnedPattern[]
    
    +isValid(): boolean
    +merge(other: StrataRegulaConfig): StrataRegulaConfig
}

class HierarchyConfig {
    +environments: string[]
    +services: string[]
    +configTypes: string[]
    
    +toSet(): DynamicHierarchy
    +fromLearning(learned: DynamicHierarchy): HierarchyConfig
}

class CompletionSettings {
    +enabled: boolean
    +triggerOnDot: boolean
    +showPatternPreview: boolean
    +maxSuggestions: number
    
    +isEnabled(): boolean
    +shouldTriggerOnDot(): boolean
}

class PatternContext {
    +currentPattern: string
    +depth: number
    +position: Position
    +isInValuePosition: boolean
    
    +getPatternParts(): string[]
    +getCurrentPart(): string
    +getExpectedType(): 'environment' | 'service' | 'configType'
}

' Relationships
StrataRegulaConfig *-- HierarchyConfig
StrataRegulaConfig *-- CompletionSettings
StrataRegulaConfig o-- LearnedPattern

DynamicHierarchy o-- LearnedPattern
HierarchyConfig ..> DynamicHierarchy : converts to/from

@enduml
```

## Activity Diagram: YAML File Analysis Process

```plantuml
@startuml YAML_Analysis_Activity

start

:Workspace file changed;
:Check if file is YAML;

if (YAML file?) then (yes)
    :Load file content;
    :Parse YAML structure;
    
    if (Valid YAML?) then (yes)
        :Traverse YAML object tree;
        
        repeat
            :Extract key-value pair;
            :Check if key matches pattern;
            
            if (StrataRegula pattern?) then (yes)
                :Parse pattern components;
                :Extract hierarchy elements;
                
                fork
                    :Update environments set;
                fork again
                    :Update services set;
                fork again
                    :Update config types set;
                fork again
                    :Update pattern frequency;
                    :Record last seen timestamp;
                end fork
                
                :Store learned pattern;
            endif
            
        repeat while (More keys?)
        
        :Build updated configuration;
        :Notify Language Server;
        :Update completion provider;
        
    else (no)
        :Log parsing error;
        :Skip file;
    endif
    
else (no)
    :Skip non-YAML file;
endif

:Analysis complete;
stop

@enduml
```

## Deployment Diagram: System Distribution

```plantuml
@startuml Deployment_Diagram

node "Developer Machine" {
    
    component "VS Code Process" {
        [Extension]
        [WebView Provider]
        [Pattern Expander UI]
    }
    
    component "Node.js LSP Process" {
        [Language Server]
        [YAML Analyzer]
        [Pattern Provider]
        [Completion Engine]
    }
    
    component "Python Process" {
        [Core Config Engine]
        [Pattern Compiler]
        [CLI Commands]
    }
    
    database "Local File System" {
        [User YAML Files]
        [Learned Patterns Cache]
        [Configuration Database]
    }
    
    database "VS Code Settings" {
        [Extension Configuration]
        [Hierarchy Settings]
        [User Preferences]
    }
}

' Communication protocols
[Extension] --> [Language Server] : JSON-RPC over IPC
[Language Server] --> [Local File System] : File I/O
[YAML Analyzer] --> [User YAML Files] : Read/Parse
[Pattern Provider] --> [Learned Patterns Cache] : Read/Write
[Core Config Engine] --> [Configuration Database] : Shared Config

' External connections (none for privacy)
note bottom of "Developer Machine"
    All processing happens locally
    No external network connections
    Complete data privacy
end note

@enduml
```

## State Diagram: Pattern Learning States

```plantuml
@startuml Pattern_Learning_States

[*] --> Idle : Extension activated

Idle --> Analyzing : YAML file opened
Idle --> Analyzing : File content changed

state Analyzing {
    [*] --> ParseYAML
    ParseYAML --> ExtractPatterns : Valid YAML
    ParseYAML --> LogError : Invalid YAML
    
    ExtractPatterns --> UpdateHierarchy : Patterns found
    ExtractPatterns --> Complete : No patterns
    
    UpdateHierarchy --> UpdateFrequency
    UpdateFrequency --> StorePatterns
    StorePatterns --> BuildConfig
    BuildConfig --> Complete
    
    LogError --> Complete
}

Analyzing --> Idle : Analysis complete
Analyzing --> Providing : Completion request during analysis

state Providing {
    [*] --> ParseContext
    ParseContext --> QueryLearned : Valid context
    ParseContext --> ReturnEmpty : Invalid context
    
    QueryLearned --> GenerateCompletions : Patterns available
    QueryLearned --> ReturnDefaults : No learned patterns
    
    GenerateCompletions --> FilterResults
    FilterResults --> RankSuggestions
    RankSuggestions --> ReturnCompletions
    
    ReturnDefaults --> ReturnCompletions
    ReturnEmpty --> [*]
    ReturnCompletions --> [*]
}

Providing --> Idle : Completions delivered

Idle --> Shutdown : Extension deactivated
Shutdown --> [*]

@enduml
```

## Communication Protocol Diagram

```plantuml
@startuml Communication_Protocol

participant "VS Code Extension\n(TypeScript)" as Ext
participant "Language Server\n(Node.js LSP)" as LSP
participant "Python Core\n(Config Engine)" as Core
participant "File System\n(Local Storage)" as FS

== Initialization Phase ==
Ext -> LSP : Start LSP process (IPC)
LSP -> FS : Load existing learned patterns
LSP -> Core : Request shared configuration
Core -> LSP : Return hierarchy config

== Pattern Learning Phase ==
FS -> LSP : File change notification
LSP -> LSP : Analyze YAML content
LSP -> FS : Store learned patterns
LSP -> Ext : Configuration updated notification

== Completion Request Phase ==
Ext -> LSP : textDocument/completion (JSON-RPC)
LSP -> LSP : Parse completion context
LSP -> FS : Query learned patterns
LSP -> LSP : Generate intelligent completions
LSP -> Ext : Return completion items

== Preview Generation Phase ==
Ext -> LSP : Custom preview request
LSP -> LSP : Expand pattern with learned data
LSP -> Ext : Return pattern expansions
Ext -> Ext : Render in WebView

== Configuration Sync Phase ==
Core -> FS : Export configuration
LSP -> FS : Import configuration updates
LSP -> Ext : Notify configuration changes

note over Ext, FS
    All communication happens locally
    No external network requests
    Privacy-preserving architecture
end note

@enduml
```

## Performance Analysis Diagram

```plantuml
@startuml Performance_Analysis

rectangle "Analysis Performance Metrics" {
    
    rectangle "YAML File Analysis" as analysis {
        - File size: 1KB - 10MB
        - Parse time: 5ms - 500ms
        - Pattern extraction: 1ms - 50ms
        - Memory usage: 100KB - 10MB
    }
    
    rectangle "Completion Response" as completion {
        - Context parsing: <1ms
        - Pattern lookup: <5ms
        - Result generation: <10ms
        - Total response: <16ms
    }
    
    rectangle "Memory Management" as memory {
        - Pattern cache: LRU with 1000 entries
        - File watching: Debounced 300ms
        - Garbage collection: Every 1000 patterns
        - Peak memory: <50MB
    }
    
    rectangle "Scalability Limits" as scale {
        - Max YAML files: 10,000
        - Max patterns: 100,000
        - Max completions: 50/request
        - Concurrent analysis: 5 files
    }
}

rectangle "Performance Optimizations" {
    
    rectangle "Incremental Processing" as incremental {
        + Only analyze changed content
        + Diff-based pattern updates
        + Lazy loading of completions
        + Progressive enhancement
    }
    
    rectangle "Caching Strategy" as caching {
        + Pattern frequency cache
        + Completion result cache
        + File content hash cache
        + Configuration state cache
    }
    
    rectangle "Async Processing" as async {
        + Non-blocking file analysis
        + Background pattern learning
        + Debounced file watching
        + Streaming completions
    }
}

analysis --> incremental : optimized by
completion --> caching : accelerated by
memory --> async : managed through

@enduml
```

## Security and Privacy Architecture

```plantuml
@startuml Security_Architecture

package "Privacy Boundaries" {
    
    rectangle "Local Processing Zone" {
        component [VS Code Extension]
        component [Language Server Process]
        component [Python Configuration Engine]
        database [Local File System]
        
        [VS Code Extension] --> [Language Server Process] : IPC (Local)
        [Language Server Process] --> [Python Configuration Engine] : File I/O (Local)
        [Language Server Process] --> [Local File System] : Read/Write (Local)
        
        note bottom : All processing happens within\nuser's local environment
    }
    
    rectangle "Network Boundary" {
        component [Internet] <<external>>
        component [Cloud Services] <<external>>
        component [External APIs] <<external>>
        
        note bottom : NO network connections\nfrom StrataRegula system
    }
}

rectangle "Data Protection Measures" {
    
    rectangle "Configuration Data" {
        - Stored locally only
        - No transmission outside machine
        - User-controlled retention
        - Automatic cleanup options
    }
    
    rectangle "Pattern Learning Data" {
        - Derived from user's own files
        - No external data sources
        - Configurable privacy settings
        - Opt-out mechanisms
    }
    
    rectangle "System Isolation" {
        - Sandboxed Language Server
        - No elevated privileges required
        - Read-only access to source files
        - Temporary data cleanup
    }
}

[Local Processing Zone] .up.> [Network Boundary] : NO CONNECTION
[Local Processing Zone] --> [Data Protection Measures] : implements

@enduml
```

This comprehensive UML documentation provides a complete technical view of the StrataRegula system architecture, covering all major components, interactions, data flows, and design decisions that support the dynamic YAML pattern learning innovation.

## System Extensibility Architecture

```plantuml
@startuml System_Extensibility

package "Core Extension Points" {
    
    interface "Plugin Interface" as PluginInterface {
        +initialize()
        +processPattern()
        +cleanup()
    }
    
    interface "Hook Interface" as HookInterface {
        +beforePatternAnalysis()
        +afterPatternAnalysis()
        +onPatternLearned()
    }
    
    interface "Extension Interface" as ExtensionInterface {
        +extendCompletions()
        +customizeValidation()
        +addCustomPatterns()
    }
}

package "Plugin System" {
    
    class "Base Plugin" as BasePlugin {
        +name: string
        +version: string
        +description: string
        
        +activate(): void
        +deactivate(): void
    }
    
    class "Pattern Plugin" as PatternPlugin {
        +patternTypes: Set<string>
        +customValidators: Map<string, Validator>
        
        +registerPatternType(type: string): void
        +addCustomValidator(pattern: string, validator: Validator): void
    }
    
    class "Hook Plugin" as HookPlugin {
        +hookPoints: Set<string>
        +callbacks: Map<string, Function>
        
        +registerHook(hookPoint: string, callback: Function): void
        +executeHook(hookPoint: string, data: any): any
    }
}

package "Extension Registry" {
    
    class "Plugin Registry" as PluginRegistry {
        +plugins: Map<string, BasePlugin>
        +activePlugins: Set<string>
        
        +registerPlugin(plugin: BasePlugin): void
        +activatePlugin(name: string): void
        +deactivatePlugin(name: string): void
        +getPlugin(name: string): BasePlugin?
    }
    
    class "Hook Registry" as HookRegistry {
        +hooks: Map<string, HookPlugin[]>
        
        +registerHook(hookPoint: string, plugin: HookPlugin): void
        +executeHooks(hookPoint: string, data: any): any[]
    }
}

package "Extension Lifecycle" {
    
    state "Extension Loading" as Loading {
        [*] --> ValidatePlugin
        ValidatePlugin --> LoadDependencies
        LoadDependencies --> InitializePlugin
        InitializePlugin --> RegisterInterfaces
        RegisterInterfaces --> [*]
    }
    
    state "Extension Execution" as Execution {
        [*] --> HookExecution
        HookExecution --> PatternProcessing
        PatternProcessing --> CustomValidation
        CustomValidation --> [*]
    }
    
    state "Extension Cleanup" as Cleanup {
        [*] --> SaveState
        SaveState --> UnregisterInterfaces
        UnregisterInterfaces --> ReleaseResources
        ReleaseResources --> [*]
    }
}

' Relationships
BasePlugin ..|> PluginInterface
PatternPlugin --|> BasePlugin
HookPlugin --|> BasePlugin

PluginRegistry --> BasePlugin : manages
HookRegistry --> HookPlugin : manages

PluginInterface --> ExtensionRegistry : registers with
HookInterface --> HookRegistry : registers with

Loading --> Execution : transitions to
Execution --> Cleanup : transitions to

@enduml
```