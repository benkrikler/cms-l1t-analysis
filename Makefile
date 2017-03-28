# simple makefile to simplify repetitive build env management tasks under posix

PYTHON := $(shell which python)
NOSETESTS := $(shell which nosetests)

all: clean setup

clean-build:
	@rm -fr build

clean-external:
	@rm -fr external

clean-so:
	@[ -d external ] && find external -name "*.so" -exec rm {} \;
	@find legacy -name "*.so" -exec rm {} \;

clean-pyc:
	@find . -name "*.pyc" -exec rm {} \;

clean: clean-build clean-so clean-pyc clean-external


# setup
setup: setup-build-dir setup-external setup-data-dir


setup-external:
	@./bin/get_l1Analysis
	@./bin/compile_l1Analysis

setup-build-dir:
	@mkdir -p build

create-data-dir:
		@mkdir -p data

setup-data-dir: create-data-dir data/L1Ntuple_test_1.root data/L1Ntuple_test_2.root data/L1Ntuple_test_3.root

data/L1Ntuple_test_1.root:
	@xrdcp root://eoscms.cern.ch//eos/cms/store/group/dpg_trigger/comm_trigger/L1Trigger/L1Menu2016/Stage2/Collision2016-wRECO-l1t-integration-v86p4/SingleMuon/crab_Collision2016-wRECO-l1t-integration-v86p4__281693_SingleMuon/161005_194247/0000/L1Ntuple_979.root data/L1Ntuple_test_1.root

data/L1Ntuple_test_2.root:
	@xrdcp root://eoscms.cern.ch//eos/cms/store/group/dpg_trigger/comm_trigger/L1Trigger/L1Menu2016/Stage2/Collision2016-wRECO-l1t-integration-v86p4/SingleMuon/crab_Collision2016-wRECO-l1t-integration-v86p4__281693_SingleMuon/161005_194247/0000/L1Ntuple_980.root data/L1Ntuple_test_2.root

data/L1Ntuple_test_3.root:
	@xrdcp root://eoscms.cern.ch//eos/cms/store/group/dpg_trigger/comm_trigger/L1Trigger/L1Menu2016/Stage2/Collision2016-wRECO-l1t-integration-v86p4/SingleMuon/crab_Collision2016-wRECO-l1t-integration-v86p4__281693_SingleMuon/161005_194247/0000/L1Ntuple_981.root data/L1Ntuple_test_3.root


# tests
pep8:
	@pep8 --exclude=.git,external examples cmsl1t

flake8:
	@flake8 cmsl1t test --ignore=F401 --max-line-length=120

# benchmarks
NTUPLE_CFG := "legacy/Config/ntuple_cfg.h"
benchmark: clean-benchmark setup-benchmark run-benchmark

clean-benchmark:
		@rm -fr benchmark

setup-benchmark:
ifeq ($(wildcard benchmark),)
	@mkdir -p benchmark/legacy
	@mkdir -p benchmark/current
endif

run-benchmark:
	@sed -i "s/return singleMuRun276243();/return benchmark_cfg();/g" $(NTUPLE_CFG)
	@time python -m memory_profiler bin/run_benchmark
	@sed -i 's/return benchmark_cfg();/return singleMuRun276243();/g' $(NTUPLE_CFG)

test: test-code flake8

test-code:
	@$(NOSETESTS) -v -a '!slow' -s test
