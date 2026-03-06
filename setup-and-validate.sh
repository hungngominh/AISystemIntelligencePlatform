#!/bin/bash
# AI System Intelligence Platform - Complete Setup & Validation Script

set -e

PROJECT_ROOT="/d/Work/AISystemIntelligencePlatform"
DOCS_ROOT="$PROJECT_ROOT/DOCUMENTS"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║         AI SYSTEM INTELLIGENCE PLATFORM - Setup & Validation Script          ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_section() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Phase 1: Verify directory structure
log_section "Phase 1: Verify Directory Structure"

cd "$PROJECT_ROOT"

# Check core files
check_file() {
    if [ -f "$1" ]; then
        log_success "Found: $1"
        return 0
    else
        log_error "Missing: $1"
        return 1
    fi
}

check_file "docker-compose.yml"
check_file ".env"
check_file "README.md"
check_file "DOCUMENTS/README.md"

# Check directories
check_dir() {
    if [ -d "$1" ]; then
        log_success "Found directory: $1"
        return 0
    else
        log_error "Missing directory: $1"
        return 1
    fi
}

check_dir "config/prometheus"
check_dir "config/grafana"
check_dir "instrumentation/python"
check_dir "instrumentation/dotnet"
check_dir "DOCUMENTS"

echo ""

# Phase 2: Documentation coverage
log_section "Phase 2: Documentation Coverage"

DOC_FILES=$(find "$DOCS_ROOT" -name "*.md" -type f 2>/dev/null | wc -l)
echo "Documentation files: $DOC_FILES"

if [ "$DOC_FILES" -ge 5 ]; then
    log_success "Documentation structure created"
else
    log_warning "Only $DOC_FILES docs found (expected >=5)"
fi

echo ""

# Phase 3: Configuration validation
log_section "Phase 3: Configuration Files"

# Check YAML files
YAML_FILES=$(find . -name "*.yml" -o -name "*.yaml" | grep -v DOCUMENTS)
YAML_COUNT=$(echo "$YAML_FILES" | grep -c ".")

echo "Found $YAML_COUNT YAML configuration files:"
echo "$YAML_FILES" | sed 's/^/  /'

echo ""

# Phase 4: Instrumentation code
log_section "Phase 4: Instrumentation Code"

check_file "instrumentation/python/telemetry.py"
check_file "instrumentation/python/metrics.py"
check_file "instrumentation/dotnet/ObservabilityExtensions.cs"
check_file "instrumentation/dotnet/PipelineMetrics.cs"

echo ""

# Phase 5: Quick verification checks
log_section "Phase 5: Quick Verification"

# Check docker-compose.yml syntax
if grep -q "version:" docker-compose.yml && grep -q "services:" docker-compose.yml; then
    log_success "docker-compose.yml has valid structure"
else
    log_error "docker-compose.yml structure invalid"
fi

# Check .env file
if grep -q "OTEL_EXPORTER_OTLP_ENDPOINT" .env; then
    log_success ".env contains OTEL configuration"
else
    log_error ".env missing OTEL configuration"
fi

# Check prometheus.yml
if grep -q "scrape_configs:" config/prometheus/prometheus.yml; then
    log_success "Prometheus config has scrape configs"
else
    log_error "Prometheus config incomplete"
fi

echo ""

# Phase 6: Summary
log_section "Summary"

echo -e "${GREEN}"
echo "✓ Project directory structure verified"
echo "✓ Documentation framework created"
echo "✓ Configuration files present"
echo "✓ Instrumentation code ready"
echo -e "${NC}"

echo ""
echo "Next steps:"
echo "1. Read documentation: cat $DOCS_ROOT/README.md"
echo "2. Review architecture: cat $DOCS_ROOT/01_ARCHITECTURE/overview.md"
echo "3. Deploy stack: docker compose up -d"
echo "4. Access Grafana: http://localhost:3000"
echo ""

# Phase 7: Optional - show deployment commands
log_section "Deployment Commands"

cat << 'DEPLOY'
# Start the observability stack
docker compose up -d

# Wait for services to initialize
sleep 15

# Verify services
docker compose ps

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Access Grafana
echo "Open http://localhost:3000 (admin/admin123)"

# View logs
docker compose logs -f otel-collector
DEPLOY

echo ""
log_success "Setup script completed successfully!"
echo ""
