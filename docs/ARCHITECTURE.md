# MCP Integration Architecture Documentation

This document describes three architectural approaches for integrating natural language queries with SD Elements via the MCP (Model Context Protocol) server.

## Overview

The goal is to enable users to interact with SD Elements using natural language queries, which are then translated into MCP tool calls and executed against the SD Elements API.

## Architecture Options

### Option A: No Claude (Maximum Performance)

**Performance:** ~1-2 seconds (fastest)  
**Complexity:** High (requires NLU/intent mapping)  
**Cost:** Lowest (no LLM calls)

#### Architecture

```
Client → MCP Proxy → Intent Mapper → MCP Server → SD Elements API
```

#### Implementation Approach

- Custom NLU/intent recognition system
- Pattern matching and entity extraction
- Direct tool invocation without LLM
- Template-based response formatting

#### Pros

- Fastest response time (~1-2s)
- Lowest cost (no LLM API calls)
- Predictable performance
- No external dependencies (beyond MCP server)

#### Cons

- Requires custom NLU/intent recognition
- Limited to predefined query patterns
- Brittle with complex or novel queries
- High maintenance burden (need to update patterns)
- Difficult to handle edge cases

#### When to Use

- High-volume, performance-critical scenarios
- Limited query patterns (e.g., specific command set)
- Cost-sensitive applications
- Environments where LLM APIs are not available

---

### Option B: Two Claude Calls (Current Client Approach)

**Performance:** ~10-12 seconds (slowest)  
**Complexity:** Low (existing implementation)  
**Cost:** Highest (two LLM calls per query)

#### Architecture

```
Client → MCP Proxy → Claude (Tool Selection) → MCP Server → SD Elements API
                                    ↓
                            Claude (Formatting) → Client
```

#### Implementation Approach

1. First Claude call: Select tool and extract arguments from natural language query
2. Execute tool via MCP server
3. Second Claude call: Format JSON result into natural language
4. Return formatted response to client

#### Pros

- Highest quality natural language responses
- Simple implementation (reuse existing client code)
- Consistent formatting across all tools
- Handles complex queries well
- Easy to maintain (Claude handles edge cases)

#### Cons

- Slowest response time (~10-12s)
- Double Claude API costs
- Double latency (two sequential API calls)
- Higher error rate (two points of failure)

#### When to Use

- User-facing chat applications
- Response quality matters more than speed
- Low-volume applications
- Prototyping and development

---

### Option C: Single Claude Call (Implemented)

**Performance:** ~3-5 seconds (balanced)  
**Complexity:** Medium  
**Cost:** Moderate (one LLM call per query)

#### Architecture

```
Client → MCP Proxy → Claude (Tool Selection) → MCP Server → SD Elements API
                                    ↓
                            Local Formatter → Client
```

#### Implementation Approach

1. Single Claude call: Select tool and extract arguments from natural language query
2. Execute tool via MCP server
3. Local formatting: Use template-based formatters to convert JSON to natural language
4. Return formatted response to client

#### Pros

- Good balance of performance and quality (~3-5s)
- 50% cost reduction vs Option B (one Claude call)
- Faster than Option B while maintaining good UX
- Template-based formatting is maintainable
- Falls back to structured JSON for unknown tools

#### Cons

- Requires maintaining formatter templates
- Formatting quality may be slightly lower than Option B
- Need to add formatters for new tools

#### When to Use

- Production applications requiring good performance
- Moderate query volume
- Balance between cost and quality
- **This is the recommended approach for most use cases**

---

## Trade-off Matrix

| Aspect | Option A (No Claude) | Option B (Two Claude) | Option C (Single Claude) |
|--------|---------------------|----------------------|-------------------------|
| **Performance** | ⭐⭐⭐⭐⭐ (1-2s) | ⭐⭐ (10-12s) | ⭐⭐⭐⭐ (3-5s) |
| **Cost** | ⭐⭐⭐⭐⭐ (Lowest) | ⭐ (Highest) | ⭐⭐⭐ (Moderate) |
| **Complexity** | ⭐ (High) | ⭐⭐⭐⭐⭐ (Low) | ⭐⭐⭐ (Medium) |
| **Maintainability** | ⭐⭐ (Low) | ⭐⭐⭐⭐⭐ (High) | ⭐⭐⭐⭐ (Good) |
| **Response Quality** | ⭐⭐ (Limited) | ⭐⭐⭐⭐⭐ (Best) | ⭐⭐⭐⭐ (Good) |
| **Flexibility** | ⭐⭐ (Low) | ⭐⭐⭐⭐⭐ (High) | ⭐⭐⭐⭐ (Good) |

## Implementation Details

### Option C Implementation (Current)

The implemented solution uses Option C and consists of:

1. **MCP Proxy Service** (`mcp-proxy-service/`)
   - Receives natural language queries
   - Uses Claude (Haiku) for tool selection
   - Executes tools via MCP server
   - Formats responses locally

2. **Mock Seaglass** (`mock-seaglass/`)
   - Simulates Seaglass service for testing
   - Forwards queries to MCP Proxy

3. **Client UI** (`client-ui/`)
   - Web interface for testing
   - Displays queries and responses

### Performance Breakdown (Option C)

- Tool list fetch: ~100ms (cached for 5 minutes)
- Claude tool selection: ~2-3s (using Haiku model)
- MCP tool execution: ~0.5-2s (depends on SD Elements API)
- Local formatting: ~10ms
- **Total: ~3-5 seconds**

### Cost Analysis

- Option A: $0 (no LLM calls)
- Option B: ~$0.01-0.02 per query (two Claude calls)
- Option C: ~$0.005-0.01 per query (one Claude call)

*Costs are approximate and depend on query complexity and model used.*

## Recommendations

1. **For Prototyping:** Use Option B (simplest, highest quality)
2. **For Production:** Use Option C (best balance)
3. **For High-Volume:** Consider Option A (if query patterns are limited)

## Future Enhancements

- **Hybrid Approach:** Use Option A for common queries, Option C for complex ones
- **Caching:** Cache tool selection results for identical queries
- **Streaming:** Stream responses for better perceived performance
- **Multi-tool Queries:** Support queries that require multiple tool calls

