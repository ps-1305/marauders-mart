#include "httplib.h"
#include "marauder_chain.h"
using json=nlohmann::json;

const std::string DBFILE = "ledger.json";

int main(){
    Chain chain;
    chain.load(DBFILE);          
    httplib::Server api;

    /* ── PASSBOOK ───────────────────────────────── */
    api.Post("/deposit", [&](const auto& req, auto& res){
        auto j=json::parse(req.body);     // {"user":"alice","amount":50}
        bool ok=chain.deposit(j["user"], j["amount"]);
        if (ok) chain.save(DBFILE);
        res.set_content(ok?R"({"status":"ok"})":R"({"status":"fail"})","application/json");
    });
    api.Post("/withdraw", [&](const auto& req, auto& res){
        auto j=json::parse(req.body);
        bool ok=chain.withdraw(j["user"], j["amount"]);
        if (ok) chain.save(DBFILE);
        res.set_content(ok?R"({"status":"ok"})":R"({"status":"fail"})","application/json");
    });
    api.Get("/balance", [&](const auto& req, auto& res){
        std::string user=req.get_param_value("user");
        json j={{"user",user},{"balance",chain.balance(user)}};
        res.set_content(j.dump(), "application/json");
    });

    /* ── ESCROW  ───────────────────────────────── */
    api.Post("/escrow/open", [&](const auto& req, auto& res){
        auto j=json::parse(req.body);  // buyer,vendor,product,delivery
        std::string id=chain.openEscrow(j["buyer"],j["vendor"],
                                        j["product"],j["delivery"]);
        if(id.empty()) res.set_content(R"({"status":"fail"})","application/json");
        else           res.set_content(json({{"status","ok"},{"id",id}}).dump(),"application/json");
    });
    api.Post("/escrow/release", [&](const auto& req, auto& res){
        auto j=json::parse(req.body);
        bool ok=chain.releaseEscrow(j["id"]);
        if (ok) chain.save(DBFILE);
        res.set_content(ok?R"({"status":"ok"})":R"({"status":"fail"})","application/json");
    });

    /* ── INTROSPECTION ─────────────────────────── */
    api.Get("/chain",   [&](auto&,auto&res){res.set_content(chain.chainJSON().dump(2),"application/json");});
    api.Get("/ledger",  [&](auto&,auto&res){res.set_content(chain.ledgerJSON().dump(2),"application/json");});
    api.Get("/escrows", [&](auto&,auto&res){res.set_content(chain.escrowsJSON().dump(2),"application/json");});

    api.listen("0.0.0.0",5173);
}