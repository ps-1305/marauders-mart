#ifndef MARAUDER_CHAIN_H
#define MARAUDER_CHAIN_H

#include <string>
#include <unordered_map>
#include <vector>
#include <ctime>
#include <sstream>
#include <iostream>
#include <fstream>
#include "json.hpp"
#include "sha256.h"            // any stand‑alone SHA‑256 header

using json = nlohmann::json;

/* ─────────────────────────────────────────── */
/*  DATA STRUCTURES                            */
/* ─────────────────────────────────────────── */
struct Tx {                      // plain transfer (deposit, withdraw, pay, fee)
    std::string from;
    std::string to;
    double      amount;          // GLX  (positive)

    json j() const { return {{"from",from},{"to",to},{"amount",amount}}; }
};

struct Escrow {
    std::string id;              // uid
    std::string buyer;
    std::string vendor;
    double      product;         // GLX → vendor on release
    double      delivery;        // GLX → platform on release
    bool        released{false};

    json j() const {
        return {{"id",id},{"buyer",buyer},{"vendor",vendor},
                {"product",product},{"delivery",delivery},{"released",released}};
    }
};

/* ─────────────────────────────────────────── */
/*  BLOCK                                      */
/* ─────────────────────────────────────────── */
struct Block {
    size_t index;
    std::time_t ts;
    std::vector<Tx>      txs;
    std::vector<Escrow>  esc;     // escrow events created or released
    std::string prevHash;
    std::string hash;

    Block(size_t idx, std::vector<Tx>  t, std::vector<Escrow> e, std::string prev)
      : index(idx), ts(std::time(nullptr)), txs(std::move(t)), esc(std::move(e)), prevHash(std::move(prev))
    {
        std::stringstream ss;
        ss<<index<<ts<<prevHash;
        for(auto &x:txs) ss<<x.from<<x.to<<x.amount;
        for(auto &e:esc) ss<<e.id<<e.released;
        hash = sha256(ss.str());
    }
    json j() const{
        json jt=json::array(); for(auto &x:txs) jt.push_back(x.j());
        json je=json::array(); for(auto &e:esc) je.push_back(e.j());
        return {{"index",index},{"ts",ts},{"prev",prevHash},{"hash",hash},
                {"txs",jt},{"esc",je}};
    }
};

/* ─────────────────────────────────────────── */
/*  CHAIN + LEDGER                             */
/* ─────────────────────────────────────────── */
class Chain {
    std::vector<Block> chain;
    std::unordered_map<std::string,double> bal;
    std::vector<Escrow> openEsc;          // still locked
    const std::string PLATFORM = "MM";    // marketplace wallet

  public:
    Chain(){
        chain.emplace_back(0,std::vector<Tx>{},std::vector<Escrow>{},"0"); // genesis
        bal[PLATFORM]=0.0;
    }
    /* ---------- BALANCE & PASSBOOK ---------- */
    bool deposit(const std::string& user,double amt){
        if(amt<=0) return false;
        bal[user]+=amt;
        addBlock({Tx{"BANK",user,amt}},{});   // BANK is virtual origin
        return true;
    }
    bool withdraw(const std::string& user,double amt){
        if(amt<=0||bal[user]<amt) return false;
        bal[user]-=amt;
        addBlock({Tx{user,"BANK",amt}},{});   // BANK virtual sink
        return true;
    }
    double balance(const std::string& user) const{
        auto it=bal.find(user);
        return it==bal.end()?0.0:it->second;
    }
    /* ---------- ESCROW ---------- */
    std::string openEscrow(const std::string& buyer,const std::string& vendor,
                           double product,double delivery){
        double total = product+delivery;
        if(bal[buyer]<total) return "";
        bal[buyer]-=total;

        std::string id = std::to_string(chain.size())+"_"+std::to_string(std::time(nullptr));
        Escrow e{id,buyer,vendor,product,delivery,false};
        openEsc.push_back(e);
        addBlock({}, {e});
        return id;
    }
    bool releaseEscrow(const std::string& id){
        for(auto &e:openEsc){
            if(e.id==id && !e.released){
                e.released=true;
                bal[e.vendor]+=e.product;
                bal[PLATFORM]+=e.delivery;
                addBlock({}, {e});          // record release event
                return true;
            }
        }
        return false;
    }
    /* ---------- SERIALISE ---------- */
    json chainJSON() const { json a=json::array(); for(auto &b:chain) a.push_back(b.j()); return a; }
    json ledgerJSON()const { json l; for(auto &kv:bal) l[kv.first]=kv.second; return l; }
    json escrowsJSON()const{
        json a=json::array();
        for(auto &e:openEsc) a.push_back(e.j());
        return a;
    }
    void save(const std::string& file) const {
        std::ofstream out(file);
        out << chainJSON().dump() << "\n"    // 1  chain
            << ledgerJSON().dump() << "\n"   // 2  ledger
            << escrowsJSON().dump()           // 3  open escrows
            ;
    }
    void load(const std::string& file){
        std::ifstream in(file);
        if(!in) return;

        json jc,jl,je;
        in >> jc >> jl >> je;

        chain.clear();
        for (auto &b : jc) {
            // rebuild Tx vector
            std::vector<Tx> txs;
            for (auto &t : b["txs"])
                txs.push_back( Tx{ t["from"], t["to"], t["amount"] } );

            // rebuild Escrow vector
            std::vector<Escrow> escs;
            for (auto &e : b["esc"])
                escs.push_back( Escrow{ e["id"], e["buyer"], e["vendor"],
                                        e["product"], e["delivery"], e["released"] } );

            chain.emplace_back( b["index"],
                                std::move(txs),
                                std::move(escs),
                                b["prev"] );
        }

        // ---------- ledger ----------
        bal.clear();
        for (auto it = jl.begin(); it != jl.end(); ++it)
            bal[it.key()] = it.value();

        // ---------- still‑open escrows ----------
        openEsc.clear();
        for (auto &e : je)
            openEsc.push_back( Escrow{ e["id"], e["buyer"], e["vendor"],
                                    e["product"], e["delivery"], e["released"] } );
    }

  private:
    void addBlock(std::vector<Tx> txs,std::vector<Escrow> esc){
        chain.emplace_back(chain.size(),std::move(txs),std::move(esc),chain.back().hash);
    }
};
#endif
